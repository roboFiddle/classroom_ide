# Generated by Django 3.0.5 on 2020-04-11 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classroom', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classroom',
            name='classroom_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
