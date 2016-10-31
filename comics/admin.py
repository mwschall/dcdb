import re

from django import forms
from django.contrib import admin

from .models import Issue, Series


class IssueAdminForm(forms.ModelForm):

    page_files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False,
    )

    class Meta:
        model = Issue
        fields = '__all__'


class IssueAdmin(admin.ModelAdmin):
    form = IssueAdminForm

    def save_model(self, request, obj, form, change):
        page_files = request.FILES.getlist('page_files')
        if form.is_valid() and page_files:
            obj.page_set.all().delete()
            obj.save()
            for f in page_files:
                # TODO: much logic improvement needed here
                m = re.search('(?P<number>\d+)\.[a-z1-9]+$', f.name, re.I)
                if m:
                    obj.page_set.create(
                        number=int(m.group('number')),
                        image=f,
                    )
                else:
                    raise forms.ValidationError('Bad files')
        else:
            obj.save()


admin.site.register(Issue, IssueAdmin)
admin.site.register(Series)
