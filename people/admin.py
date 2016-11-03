from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import Credit, Entity, Role


class CreditInline(GenericTabularInline):
    model = Credit
    extra = 1


admin.site.register(Role)
admin.site.register(Entity)
