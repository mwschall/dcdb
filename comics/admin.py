import re

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction

from people.admin import CreditInline
from .models import Installment, Story, SourceImage


class StoryAdmin(admin.ModelAdmin):
    inlines = [CreditInline]


def parse_pages(obj, page_files):
    obj.has_cover = False
    info = []

    for f in page_files:
        if re.search('cover', f.name):
            obj.has_cover = True
            info.append({
                'number': 0,
                'file': f,
            })
        else:
            m = re.search('(?P<number>\d+)\.[a-z1-9]+$', f.name, re.I)
            if m:
                number = int(m.group('number'))
                if number is 0:
                    obj.has_cover = True
                info.append({
                    'number': number,
                    'file': f,
                })

    # assume single images are a strip or one-panel affair
    if len(info) <= 1:
        obj.has_cover = False

    info.sort(key=lambda p: p['number'])
    return info


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
        if not form.is_valid():
            raise ValidationError('wut?')
        elif page_files:
            pages = parse_pages(obj, page_files)

            obj.page_set.all().delete()
            obj.save()

            for idx, p in enumerate(pages):
                page = obj.page_set.create(
                    order=idx,
                    number=p['number'],
                )
                image = SourceImage(
                    owner=page,
                    file=p['file'],
                    original_name=p['file'].name,
                )
                image.save()
        else:
            obj.save()


admin.site.register(Story, StoryAdmin)
admin.site.register(Installment, InstallmentAdmin)
