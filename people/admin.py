from adminsortable2.admin import SortableInlineAdminMixin
from django.contrib import admin

from .models import Entity, Role, EntityUrl


class EntityUrlInline(SortableInlineAdminMixin, admin.TabularInline):
    classes = ['collapse']
    model = EntityUrl
    extra = 0


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    search_fields = ('working_name',)
    inlines = (EntityUrlInline,)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass
