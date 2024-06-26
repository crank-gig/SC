# Generated by Django 5.0.3 on 2024-04-09 07:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coinstackcapital', '0009_remove_myuser_logs_requestlog_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestlog',
            name='status',
            field=models.CharField(blank=True, choices=[('Untouched', 'Untouched'), ('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Untouched', max_length=9),
        ),
        migrations.AlterField(
            model_name='requestlog',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='request_logs', to=settings.AUTH_USER_MODEL),
        ),
    ]
