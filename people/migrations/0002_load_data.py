from django.db import migrations

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
    role_model = apps.get_model('people', 'Role')
    pk = 0
    for role in ROLES:
        pk += 1
        vr = role_model(pk, *role)
        vr.save()


def drop_roles(apps, schema_editor):
    role_model = apps.get_model('people', 'Role')
    role_model.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('people', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            populate_roles,
            drop_roles,
        ),
    ]
