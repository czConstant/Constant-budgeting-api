# Generated by Django 3.1.4 on 2021-02-03 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SubLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_id', models.IntegerField(null=True)),
                ('task', models.CharField(max_length=100)),
                ('message_id', models.BigIntegerField()),
                ('data', models.TextField(null=True)),
                ('response', models.TextField(null=True)),
                ('status', models.CharField(choices=[('success', 'Success'), ('failed', 'Failed'), ('pending', 'Pending')], default='pending', max_length=50)),
            ],
        ),
        migrations.AddIndex(
            model_name='sublog',
            index=models.Index(fields=['message_id'], name='budgeting_p_message_31c178_idx'),
        ),
        migrations.AddIndex(
            model_name='sublog',
            index=models.Index(fields=['message_id', 'task'], name='budgeting_p_message_7920b9_idx'),
        ),
        migrations.AddIndex(
            model_name='sublog',
            index=models.Index(fields=['message_id', 'user_id'], name='budgeting_p_message_de30b3_idx'),
        ),
    ]