# Generated by Django 3.1.4 on 2021-02-17 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budgeting', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='note',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
