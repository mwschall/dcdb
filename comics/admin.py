import math
import re
from decimal import Decimal
from io import BytesIO
from os.path import splitext

from PIL import Image
from PyPDF2 import PdfFileReader
from adminsortable2.admin import SortableInlineAdminMixin
from django import forms
from django.contrib import admin
from django.contrib.admin import TabularInline
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db import transaction
from django.db.models import Window, F, Max
from django.db.models.functions import RowNumber
from django.forms import Textarea

from comics.forms import NumeralField, InstallmentFileField
from comics.util import is_model_request, get_upload_fp
from comics.validators import ARCHIVE_EXTS
from .models import Installment, Series, Thread, ThreadSequence, Page, InstallmentLabel


def is_series_request(request):
    return is_model_request(request, Series)


#########################################
# Installment Form                      #
#########################################

class InstallmentAdminForm(forms.ModelForm):
    page_files = InstallmentFileField(
        required=False,
    )
    number = NumeralField(
        required=False,
        first_length=Installment.FIRST_NUMBER,
        second_length=Installment.SECOND_NUMBER,
    )
    title = forms.CharField(
        required=False,
        strip=True,
    )

    class Meta:
        model = Installment
        fields = (
            'series',
            'number',
            'title',
            'synopsis',
            'release_datetime',
            'page_files',
            'has_cover',
        )

    def _clean_form(self):
        super()._clean_form()
        if self.cleaned_data.get('number') is None and not self.cleaned_data['title']:
            self.add_error('number', ValidationError('A number is required if no title is specified.'))

    def _post_clean(self):
        super()._post_clean()
        if hasattr(self.files, 'getlist'):
            page_files = self.files.getlist('page_files')
            if not page_files:
                return

            file_exts = {splitext(f.name)[1] for f in page_files}

            if len(page_files) > 1 and file_exts & ARCHIVE_EXTS:
                raise ValidationError('Only one archive file at a time is accepted.')

            if '.pdf' in file_exts:
                self.instance.page_count = PdfFileReader(get_upload_fp(page_files[0])).getNumPages()
            elif '.zip' in file_exts:
                raise ValidationError('Zip unpacking not implemented.')
            else:
                self.instance.page_count = len(page_files)


#########################################
# InstallmentLabel Admin                #
#########################################

@admin.register(InstallmentLabel)
class InstallmentLabelAdmin(admin.ModelAdmin):
    search_fields = ('value',)

    def has_change_permission(self, request, obj=None):
        if is_series_request(request):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if is_series_request(request):
            return False
        return super().has_delete_permission(request, obj)


#########################################
# Series Admin                          #
#########################################

def parse_pages(page_files):
    has_cover = False
    pages = []

    for f in page_files:
        if re.search('cover', f.name):
            has_cover = True
            pages.append({
                'number': 0,
                'file': f,
            })
        else:
            m = re.search(r'^(?P<label>(?:[-_a-z\s]+(?:\d+[-_\s]+)?)?0*(?P<number>\d+)).*\.(?P<ext>[a-z1-9]+)$', f.name, re.I)
            if m:
                number = int(m.group('number'))
                if number is 0:
                    has_cover = True

                label = m.group('label')[1:]
                if label[0] == 'i' or label[0] == 'p':
                    label = str(number)
                else:
                    label = label[0] + str(number)

                pages.append({
                    'label': label,
                    'number': number,
                    'file': f,
                })

    # assume single images are a strip or one-panel affair
    if len(pages) <= 1:
        has_cover = False

    return pages, has_cover


class InstallmentInline(SortableInlineAdminMixin, TabularInline):
    model = Installment
    form = InstallmentAdminForm
    max_num = 0
    extra = 0
    show_change_link = True

    fields = (
        'number',
        'title',
        'release_datetime',
    )


class SeriesAdminForm(forms.ModelForm):
    strip_files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True, 'accept': 'image/*'}),
        required=False,
    )

    class Meta:
        model = Series
        fields = (
            'name',
            'slug',
            'installment_label',
            'flip_direction',
            'strip_files',
            'is_strip',
        )


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    form = SeriesAdminForm
    inlines = [InstallmentInline]

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        strip_files = request.FILES.getlist('strip_files')
        if not form.is_valid():
            raise ValidationError('wut?')
        elif strip_files:
            pages, has_cover = parse_pages(strip_files)
            pages.sort(key=lambda pi: pi['file'].name)

            obj.is_strip = True
            obj.installments.all().delete()
            obj.save()

            for idx, p in enumerate(pages):
                ins = obj.installments.create(
                    number=p['label'],
                    has_cover=False,
                )
                # TODO: is there some better way to create this?
                ins.page = Page.objects.create(
                    installment=ins,
                    order=0,
                    file=p['file'],
                    original_name=p['file'].name,
                )
                ins.save()
        else:
            obj.save()


#########################################
# Installment Admin                     #
#########################################

# https://stackoverflow.com/a/34116472
def parse_pdf(pdf_file):
    pages = []
    pdf = PdfFileReader(get_upload_fp(pdf_file))

    # TODO: shunt complex pages to poppler rather than erroring out
    # TODO: make use of /ColorSpace resources in Pillow

    for i, page in enumerate(pdf.pages):
        x_object = page['/Resources']['/XObject'].getObject()

        if '/Text' in page['/Resources']['/ProcSet']:
            raise ValueError('Page %d specifies a /Text process.' % i)

        obj = None
        for o in x_object:
            if x_object[o]['/Subtype'] == '/Image':
                if obj:
                    raise ValueError('Page %d has multiple images.' % i)
                obj = o

        if not obj:
            raise ValueError('Page %d has no image.' % i)

        fltr = x_object[obj]['/Filter']
        size = (x_object[obj]['/Width'], x_object[obj]['/Height'])
        data = x_object[obj].getData()
        if x_object[obj]['/ColorSpace'] == '/DeviceRGB':
            mode = "RGB"
        else:
            mode = "P"

        buf = BytesIO()

        if '/FlateDecode' in fltr:
            x_object[obj] = Image.frombytes(mode, size, data)
            x_object[obj].save(buf, 'PNG', optimize=True)
            ext = ".pdf"
            ct = 'image/png'
        elif '/DCTDecode' in fltr:
            buf.write(data)
            ext = ".jpg"
            ct = 'image/jpeg'
        elif '/JPXDecode' in fltr:
            buf.write(data)
            ext = ".jpx"
            ct = 'image/jpx'
        else:
            raise NotImplementedError('/Filter = %s not supported.' % fltr)

        name = 'page_{:04d}{}'.format(i, ext)
        pages.append({
            'number': i,
            'file': InMemoryUploadedFile(buf, None, name, ct, buf.tell(), None),
        })

    return pages, True


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    form = InstallmentAdminForm
    autocomplete_fields = ('series',)
    readonly_fields = ('has_cover',)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if initial.get('series') and not initial.get('number'):
            qs = Installment.objects.filter(series=initial['series'])
            curr = qs.aggregate(Max('number'))['number__max']
            # don't make assumptions if no existing numbers
            if curr is not None:
                if curr == math.floor(curr):
                    initial['number'] = curr + 1
                else:
                    dec = 1 / Decimal(pow(10, Installment.SECOND_NUMBER))
                    initial['number'] = curr + dec
        return initial

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        page_files = request.FILES.getlist('page_files')
        if page_files:
            ext = splitext(page_files[0].name)[1]
            if ext == '.pdf':
                pages, has_cover = parse_pdf(page_files[0])
            else:
                pages, has_cover = parse_pages(page_files)
            pages.sort(key=lambda pi: pi['number'])

            obj.has_cover = has_cover
            obj.pages.all().delete()
            obj.save()

            for idx, p in enumerate(pages):
                obj.pages.create(
                    order=idx,
                    file=p['file'],
                    original_name=p['file'].name,
                )
        else:
            obj.save()

        # avoid work if we can
        if change and 'number' not in form.changed_data:
            return

        # can't make good assumptions without a number
        if obj.number is None:
            # put last if new, otherwise leave in place
            if not change:
                obj.ordinal = obj.series.installments.count()
                obj.save(update_fields=['ordinal'])
            return

        # put last if "latest"
        if not change:
            agg = obj.series.installments.all().aggregate(Max('number'))
            if obj.number == agg['number__max']:
                obj.ordinal = obj.series.installments.count()
                obj.save(update_fields=['ordinal'])
                return

        # sort Installments in this Series in something like their natural order
        qs = obj.series.installments \
            .annotate(natural_ordinal=Window(expression=RowNumber(),
                                             order_by=[F('number').asc(),
                                                       F('title').asc()])) \
            .order_by('natural_ordinal') \
            .values_list('pk', 'ordinal')

        # find the ordinal of the natural previous element
        # NOTE: would rather do this in the DB, but I don't know how without raw SQL
        obj_ordinal = 0
        for t in qs:
            if t[0] == obj.pk:
                break
            obj_ordinal = t[1]
        obj_ordinal += 1

        # insert object right after its natural predecessor
        obj.series.installments \
            .filter(ordinal__gte=obj_ordinal) \
            .update(ordinal=F('order') + 1)
        obj.ordinal = obj_ordinal
        obj.save(update_fields=['ordinal'])


#########################################
# Thread Admin                          #
#########################################

class ThreadSequenceInline(TabularInline):
    model = ThreadSequence
    extra = 1


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    inlines = [ThreadSequenceInline]
    formfield_overrides = {
        models.TextField: {
            'widget': Textarea(
                attrs={'rows': 3,
                       'cols': 60}
            )
        },
    }
