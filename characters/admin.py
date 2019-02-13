import re

from adminsortable2.admin import SortableAdminMixin
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models, transaction
from django.db.models import F, When, Case, Value
from django.forms import widgets
from django.forms.formsets import DELETION_FIELD_NAME

from characters.models import Persona, Appearance, Being, Classification
from comics.admin import InstallmentAdmin
from comics.models import Installment

# TODO: find a better place for this
MAX_ORD = 32767


def is_model_request(request, model):
    ct = ContentType.objects.get_for_model(model)
    return re.search('/{}/{}/'.format(ct.app_label, ct.model), request.path)


def is_being_request(request):
    return is_model_request(request, Being)


def is_persona_request(request):
    return is_model_request(request, Persona)


def aka(obj):
    return ', '.join(obj.aka.values_list('name', flat=True))


def creators(obj):
    return ', '.join(obj.creators.values_list('working_name', flat=True))
creators.short_description = 'Creator(s)'


#########################################
# Classification Admin                  #
#########################################

@admin.register(Classification)
class ClassificationAdmin(SortableAdminMixin, admin.ModelAdmin):
    # disable RelatedFieldWidgetWrapper buttons for a cleaner interface
    def has_add_permission(self, request):
        if is_being_request(request):
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if is_being_request(request):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if is_being_request(request):
            return False
        return super().has_delete_permission(request, obj)


#########################################
# Being Admin                           #
#########################################

class TabularRadioInput(widgets.Input):
    input_type = 'radio'
    # NOTE: The JavaScript depends on this value.
    class_name = 'tabular-radio'

    def get_link_name(self, name):
        # use only the letter portion, not including the row index
        return name[:name.find('-')+1] + self.class_name

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['name'] = self.get_link_name(name)
        context['widget']['value'] = name[:name.rfind('-')]  # whole prefix
        if value:
            context['widget']['attrs']['checked'] = True
        return context

    def value_from_datadict(self, data, files, name):
        val = data.get(self.get_link_name(name))  # whole prefix
        # NOTE: the trailing dash is important as a delimiter
        return bool(re.search('^{}-'.format(val), name))

    def value_omitted_from_data(self, data, files, name):
        return False


class TabularRadioField(forms.Field):
    widget = TabularRadioInput


class PersonaInlineForm(forms.ModelForm):
    is_primary = TabularRadioField(required=False)

    class Meta:
        model = Persona
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, 'instance'):
            self.initial['is_primary'] = self.instance.is_primary

    def _clean_form(self):
        super()._clean_form()
        if self.cleaned_data:
            if self.cleaned_data.get('is_primary', False) and self.cleaned_data.get(DELETION_FIELD_NAME, False):
                self.add_error(None, ValidationError('Cannot delete the Primary Persona.'))

    def _post_clean(self):
        super()._post_clean()
        self.instance.is_primary = self.cleaned_data.get('is_primary', False)

    def _save_m2m(self):
        super()._save_m2m()
        # seemed simpler to do this here rather than in save_related
        persona = self.instance
        if persona.is_primary and persona.being.primary_persona != self:
            persona.being.primary_persona = persona
            persona.being.save(update_fields=['primary_persona'])


class PersonaInlineFormset(forms.BaseInlineFormSet):
    # errors are ignored on forms marked for deletion so this check is needed
    def _should_delete_form(self, form):
        return super()._should_delete_form(form) \
            and not form.cleaned_data.get('is_primary', False)


class PersonaInline(admin.TabularInline):
    is_primary = models.IntegerField()

    model = Persona
    form = PersonaInlineForm
    formset = PersonaInlineFormset
    min_num = 1
    extra = 0

    fields = (
        'name',
        'classification',
        'type',
        'creators',
        'is_primary',
    )
    autocomplete_fields = ('creators',)
    show_change_link = True

    def get_formset(self, request, obj=None, **kwargs):
        return super().get_formset(request, obj=obj, validate_min=True, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .annotate(is_primary=Case(
                When(pk=F('being__primary_persona__pk'), then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField(),
            )) \
            .order_by('-is_primary', 'name')


class BeingForm(forms.ModelForm):
    primary_name = forms.CharField(label='Name', required=False, disabled=True)
    primary_row = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Being
        fields = (
            'primary_name',
            'bio',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # dunno if there is a better way to do this...
        self.initial['primary_name'] = str(self.instance)


@admin.register(Being)
class BeingAdmin(admin.ModelAdmin):
    list_display = ('name', aka, creators)
    search_fields = (
        'personas__name',
        'personas__creators__working_name',
        'personas__classification__name',
    )
    form = BeingForm

    inlines = (PersonaInline,)
    exclude = ('primary_persona',)

    # TODO: optimize list_display queries

    def has_add_permission(self, request):
        if is_persona_request(request):
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if is_persona_request(request):
            return False
        return super().has_change_permission(request, obj)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # cross-populate creators
        being = form.instance
        orphans = being.personas.filter(creators=None)
        if orphans:
            default_creators = being.primary_persona.creators.all()
            # things get non-deterministic if we reach beyond the primary persona
            if default_creators:
                for o in orphans:
                    o.creators.set(default_creators)


#########################################
# Persona Admin                         #
#########################################

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('name', 'cls_name', aka, creators)
    search_fields = (
        'name',
        'being__primary_persona__name',
        'classification__name',
        'creators__working_name',
    )

    def cls_name(self, obj):
        return obj.cls_name
    cls_name.short_description = 'Classification'
    cls_name.admin_order_field = 'classification__order'

    # TODO: need to add a change link for Being somehow without making the field editable

    fields = (
        'being',
        'name',
        'type',
        'classification',
        'creators',
    )
    autocomplete_fields = ('being', 'creators')

    # TODO: optimize list_display queries

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('being',)
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        # cannot delete primary personas
        if is_being_request(request) or obj is not None and not obj.is_primary:
            return super().has_delete_permission(request, obj)
        return False


#########################################
# Installment Admin (Mod)               #
#########################################

class AppearanceInlineForm(forms.ModelForm):
    begin_ord = forms.IntegerField(min_value=0, required=True)
    end_ord = forms.IntegerField(min_value=0, required=True)

    class Meta:
        model = Appearance
        fields = (
            'persona',
            'begin_ord',
            'end_ord',
            'type',
        )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        instance = kwargs.get("instance", None)

        if instance is not None and hasattr(instance, 'begin_ord'):
            initial['begin_ord'] = instance.begin_ord
            initial['end_ord'] = instance.end_ord
            kwargs['initial'] = initial

        super().__init__(*args, **kwargs)

    def _clean_form(self):
        super()._clean_form()
        if self.cleaned_data.get('begin_ord', 0) > self.cleaned_data.get('end_ord', MAX_ORD):
            self.add_error(None, ValidationError('Invalid page ordinal range: begin > end.'))


class AppearanceInlineFormset(forms.BaseInlineFormSet):
    # NOTE: Django supports Window functions, but I gave up trying to make an equivalent query happen.
    # https://stackoverflow.com/a/17046749
    def get_queryset(self):
        if not hasattr(self, '_queryset'):
            self._queryset = Appearance.objects \
                .raw('''
                WITH    T
                        AS (SELECT  ROW_NUMBER() OVER (ORDER BY cp."order") - cp."order" AS grp,
                                    cp."order" AS ordinal,
                                    ca.*
                            FROM    characters_appearance AS ca 
                                    INNER JOIN comics_page AS cp
                                    ON ca.page_id = cp.sourceimage_ptr_id
                            WHERE   ca.installment_id = %s)
                SELECT 	id,
                        persona_id,
                        installment_id,
                        page_id,
                        type,
                        MIN(ordinal) AS begin_ord,
                        MAX(ordinal) AS end_ord
                FROM   	T
                GROUP  	BY grp, type
                ORDER  	BY MIN(ordinal)  /* TODO: also by persona name and/or end_ord) */
                ''', [self.instance.pk])
        return self._queryset

    def full_clean(self):
        last_ord = self.instance.pages.count() - 1
        msg = 'There are only %(limit_value)s pages.'

        # safer and better to not assume full_clean will be called only once
        def monkey_patch(validators):
            mvv = next(filter(lambda v: isinstance(v, MaxValueValidator), validators), None)
            if not mvv:
                mvv = MaxValueValidator(last_ord, message=msg)
                validators.append(mvv)
            else:
                mvv.limit_value = last_ord

        # monkey patch these fields now that we know the page count
        for i in range(0, self.total_form_count()):
            fields = self.forms[i].fields
            monkey_patch(fields['begin_ord'].validators)
            monkey_patch(fields['end_ord'].validators)

        super().full_clean()

    def clean(self):
        super().clean()
        if not self.is_valid():
            return

        range_data = [(f['persona'], f['begin_ord'], f['end_ord'])
                      for f in sorted([cd for cd in self.cleaned_data
                                       if cd and cd.get('persona') and not cd.get(DELETION_FIELD_NAME)],
                                      key=lambda k: (k['persona'].id, k['begin_ord']))]

        prev = None
        for data in range_data:
            persona, a_begin, a_end = data
            if prev and persona == prev[0] and a_begin <= prev[2]:
                raise ValidationError(
                    'Overlapping appearance ranges for %(name)s.',
                    params={'name': persona}
                )
            prev = data

    @transaction.atomic
    def save(self, commit=True):
        # these are expected
        self.new_objects = []
        self.changed_objects = []
        self.deleted_objects = []

        if not self.initial_forms:
            return []

        if not any([form.has_changed() for form in self.initial_forms]) and \
                not any([form.has_changed() for form in self.extra_forms]):
            return []

        # expand ranges into individual appearances
        page_ids = self.instance.pages.values_list('pk', flat=True)
        appearances = []
        for form in self.forms:
            data = form.cleaned_data
            if data[DELETION_FIELD_NAME]:
                continue
            appearances += [Appearance(persona=data['persona'],
                                       installment=data['installment'],
                                       page_id=page_ids[o],
                                       type=data['type'])
                            for o in range(data['begin_ord'], data['end_ord'] + 1)]

        # updating is too complicated, so frag everything and do-over fresh
        self.instance.appearances.all().delete()
        return self.instance.appearances.bulk_create(appearances)


class AppearancesInline(admin.TabularInline):
    begin_ord = models.PositiveSmallIntegerField()
    end_ord = models.PositiveSmallIntegerField()

    model = Appearance
    form = AppearanceInlineForm
    formset = AppearanceInlineFormset
    extra = 0

    autocomplete_fields = ('persona',)


class ModInstallmentAdmin(InstallmentAdmin):
    inlines = InstallmentAdmin.inlines + [AppearancesInline]


admin.site.unregister(Installment)
admin.site.register(Installment, ModInstallmentAdmin)
