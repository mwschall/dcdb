import re

from django import forms
from django.contrib import admin
from django.contrib.admin import TabularInline
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.forms import Textarea

from people.admin import CreditInline
from .models import Installment, Series, Thread, ThreadSequence, Page


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
            m = re.search('(?P<label>(?:\W[a-z])?0*(?P<number>\d+))\.(?P<ext>[a-z1-9]+)$', f.name, re.I)
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
            'flip_direction',
            'strip_files',
            'is_strip',
        )


class SeriesAdmin(admin.ModelAdmin):
    form = SeriesAdminForm
    inlines = [CreditInline]

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


class InstallmentAdminForm(forms.ModelForm):
    page_files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False,
    )

    class Meta:
        model = Installment
        fields = '__all__'


class InstallmentAdmin(admin.ModelAdmin):
    form = InstallmentAdminForm
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


class ThreadSequenceInline(TabularInline):
    model = ThreadSequence
    extra = 1


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


admin.site.register(Installment, InstallmentAdmin)
admin.site.register(Series, SeriesAdmin)
admin.site.register(Thread, ThreadAdmin)
