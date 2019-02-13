from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import Credit, Entity, Role


class CreditInline(GenericTabularInline):
    model = Credit
    extra = 1


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    search_fields = ('working_name',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass
