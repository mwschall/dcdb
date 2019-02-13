from django.db import migrations

CLASSIFICATIONS = (
    ['human'],
    ['humanoid'],

    ['demi-god'],
    ['god'],

    ['metaphysical'],
)


def populate_clses(apps, schema_editor):
    cls_model = apps.get_model('characters', 'Classification')
    pk = 0
    for cls, order in CLASSIFICATIONS:
        pk += 1
        vr = cls_model(pk, order=order, *cls)
        vr.save()


def drop_clses(apps, schema_editor):
    cls_model = apps.get_model('characters', 'Classification')
    cls_model.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('characters', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            populate_clses,
            drop_clses,
        ),
    ]
