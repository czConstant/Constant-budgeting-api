# Generated by Django 3.1.4 on 2021-02-19 07:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budgeting', '0005_auto_20210219_0448'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='currency',
            field=models.CharField(default='USD', max_length=10),
        ),
        migrations.AddField(
            model_name='transaction',
            name='external_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
