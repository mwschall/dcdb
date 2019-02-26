# Generated by Django 2.1.5 on 2019-02-19 03:56

from django.db import migrations


#########################################
# Installment Labels                    #
#########################################

LABELS = (
    ['#'],
    ['chapter'],
    ['issue'],
    ['part'],
)


def populate_labels(apps, schema_editor):
    model = apps.get_model('comics', 'InstallmentLabel')
    pk = 0
    for label in LABELS:
        pk += 1
        obj = model(pk, *label)
        obj.save()


def drop_labels(apps, schema_editor):
    model = apps.get_model('comics', 'InstallmentLabel')
    model.objects.all().delete()


#########################################
# Migration                             #
#########################################

class Migration(migrations.Migration):

    dependencies = [
        ('comics', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            populate_labels,
            drop_labels,
        )
    ]