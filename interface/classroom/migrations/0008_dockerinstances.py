# Generated by Django 3.0.5 on 2020-04-12 06:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classroom', '0007_auto_20200412_0609'),
    ]

    operations = [
        migrations.CreateModel(
            name='DockerInstances',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('port', models.IntegerField()),
            ],
        ),
    ]
