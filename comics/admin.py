import re

from django import forms
from django.contrib import admin
from django.contrib.admin import TabularInline
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.forms import Textarea

from comics.util import is_model_request
from .models import Installment, Series, Thread, ThreadSequence, Page, InstallmentLabel


def is_series_request(request):
    return is_model_request(request, Series)


#########################################
# Installment Form                      #
#########################################

class InstallmentAdminForm(forms.ModelForm):
    page_files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False,
    )

    class Meta:
        model = Installment
        fields = '__all__'

    def _post_clean(self):
        super()._post_clean()
        page_files = self.files.getlist('page_files')
        if page_files:
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


class SeriesAdminForm(forms.ModelForm):
    strip_files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
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

@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    form = InstallmentAdminForm
    autocomplete_fields = ('series',)
    readonly_fields = ('has_cover',)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        page_files = request.FILES.getlist('page_files')
        if page_files:
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
