# Generated by Django 3.1.4 on 2021-02-25 08:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budgeting', '0012_auto_20210223_1102'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField()),
                ('wallet_id', models.IntegerField()),
                ('category_id', models.IntegerField()),
                ('category_code', models.CharField(max_length=255)),
                ('category_name', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=18)),
                ('current_amount', models.DecimalField(decimal_places=2, max_digits=18)),
                ('from_date', models.DateField()),
                ('to_date', models.DateField()),
                ('is_end', models.BooleanField()),
                ('is_over', models.BooleanField()),
            ],
            options={
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TransactionByCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=18)),
                ('category_id', models.IntegerField()),
                ('category_code', models.CharField(max_length=255)),
                ('category_name', models.CharField(max_length=255)),
            ],
            options={
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=18)),
                ('from_date', models.DateField()),
                ('to_date', models.DateField()),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='category_budgets', to='budgeting.category')),
                ('wallet', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wallet_budgets', to='budgeting.wallet')),
            ],
        ),
    ]