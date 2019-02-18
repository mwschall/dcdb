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
    role_model = apps.get_model('metadata', 'Role')
    pk = 0
    for role in ROLES:
        pk += 1
        vr = role_model(pk, *role)
        vr.save()


def drop_roles(apps, schema_editor):
    role_model = apps.get_model('metadata', 'Role')
    role_model.objects.all().delete()


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
    cls_model = apps.get_model('metadata', 'Classification')
    pk = 0
    for order, cls in enumerate(CLASSIFICATIONS):
        pk += 1
        vr = cls_model(pk, order=order, *cls)
        vr.save()


def drop_clses(apps, schema_editor):
    cls_model = apps.get_model('metadata', 'Classification')
    cls_model.objects.all().delete()


#########################################
# Migrations                            #
#########################################

def up(apps, schema_editor):
    populate_roles(apps, schema_editor)
    populate_clses(apps, schema_editor)


def down(apps, schema_editor):
    drop_clses(apps, schema_editor)
    drop_roles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            up,
            down,
        ),
    ]
