from django.db import migrations


#########################################
# Default Roles                         #
#########################################

ROLES = (
    ['writer'],

    ['artist'],
    ['inker'],
    ['colorist'],
    ['post'],
    ['typesetter'],

    ['cover'],

    ['editor'],
)


def populate_roles(apps, schema_editor):
    model = apps.get_model('metadata', 'Role')
    pk = 0
    for role in ROLES:
        pk += 1
        obj = model(pk, order=pk, *role)
        obj.save()


def drop_roles(apps, schema_editor):
    model = apps.get_model('metadata', 'Role')
    model.objects.all().delete()


#########################################
# Default Classifications               #
#########################################

CLASSIFICATIONS = (
    ['human'],
    ['humanoid'],

    ['cyborg'],
    ['robot'],
    ['ai'],

    ['demi-god'],
    ['god'],

    ['metaphysical'],  # Death, etc.
)


def populate_clses(apps, schema_editor):
    model = apps.get_model('metadata', 'Classification')
    pk = 0
    for cls in CLASSIFICATIONS:
        pk += 1
        obj = model(pk, order=pk, *cls)
        obj.save()


def drop_clses(apps, schema_editor):
    model = apps.get_model('metadata', 'Classification')
    model.objects.all().delete()


#########################################
# Migration                             #
#########################################

class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            populate_roles,
            drop_roles,
        ),
        migrations.RunPython(
            populate_clses,
            drop_clses,
        ),
    ]
