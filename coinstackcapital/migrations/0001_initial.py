# Generated by Django 5.0.3 on 2024-03-09 10:39

import django.db.models.deletion
import secrets
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MyUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=255, unique=True, verbose_name='email address')),
                ('username', models.CharField(blank=True, max_length=255, unique=True, verbose_name='Username')),
                ('first_name', models.CharField(blank=True, max_length=50, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, max_length=50, verbose_name='Last name')),
                ('other_names', models.CharField(blank=True, max_length=100, verbose_name='Other names')),
                ('date_of_birth', models.DateField(blank=True, null=True, verbose_name='Date of Birth')),
                ('kyc_status', models.CharField(blank=True, choices=[('Untouched', 'Untouched'), ('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Untouched', max_length=9)),
                ('account_status', models.CharField(blank=True, choices=[('Active', 'Active'), ('Suspended', 'Suspended'), ('Banned', 'Banned')], default='Active', max_length=9)),
                ('misc', models.JSONField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_admin', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Auth_Data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_card', models.FileField(blank=True, upload_to='uploads/', verbose_name='ID Card')),
                ('passport', models.FileField(blank=True, upload_to='uploads/', verbose_name='Passport')),
                ('drivers_license', models.FileField(blank=True, upload_to='uploads/', verbose_name="Driver's License")),
                ('voters_card', models.FileField(blank=True, upload_to='uploads/', verbose_name="Voter's Card")),
                ('bank_statement', models.FileField(blank=True, upload_to='uploads/', verbose_name='Bank Statement')),
                ('utility_bill', models.FileField(blank=True, upload_to='uploads/', verbose_name='Utility Bill')),
                ('log', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='DropDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('client_secret', models.CharField(default=secrets.token_urlsafe, editable=False, max_length=50, unique=True)),
                ('redirect_url', models.URLField(blank=True)),
                ('callback_url', models.URLField(blank=True)),
                ('pay_details', models.JSONField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='EmailMisc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_address', models.EmailField(blank=True, max_length=254)),
                ('email_code', models.CharField(blank=True, max_length=255)),
                ('email_code_time', models.DateTimeField(blank=True)),
                ('email_link', models.URLField(blank=True)),
                ('email_link_time', models.DateTimeField(blank=True)),
                ('reason', models.CharField(blank=True, choices=[('email-verification', 'Email Verification'), ('password-change', 'Password Change'), ('verified', 'verified')], max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='RateLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('rate_limit_reset', models.DateTimeField()),
                ('rate_limit_remaining', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Referral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('referral_code', models.CharField(blank=True, max_length=50)),
                ('referral_link', models.CharField(blank=True, max_length=50)),
                ('rewards', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='RequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_agent', models.CharField(max_length=255)),
                ('referrer', models.CharField(blank=True, max_length=255, null=True)),
                ('http_method', models.CharField(max_length=10)),
                ('request_url', models.URLField()),
                ('request_header', models.TextField()),
                ('client_ip_address', models.GenericIPAddressField()),
                ('geolocation_data', models.JSONField(blank=True, null=True)),
                ('date_time', models.DateTimeField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Security_Settings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('two_factor_auth_preferences', models.JSONField(blank=True)),
                ('security_questions', models.JSONField(blank=True)),
                ('email_notif_settings', models.JSONField(blank=True)),
                ('sms_notif_settings', models.JSONField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street', models.CharField(blank=True, max_length=50, verbose_name='Street')),
                ('city', models.CharField(blank=True, max_length=50, verbose_name='City')),
                ('state_or_province', models.CharField(blank=True, max_length=50, verbose_name='State/Province')),
                ('county', models.CharField(blank=True, max_length=50, verbose_name='County')),
                ('postal_or_zip', models.PositiveSmallIntegerField(blank=True, verbose_name='Postal/Zip Code')),
                ('Country', models.CharField(blank=True, max_length=50, verbose_name='Country')),
                ('addresse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='myuser',
            name='auth_data',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coinstackcapital.auth_data'),
        ),
        migrations.AddField(
            model_name='myuser',
            name='drop_client',
            field=models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, to='coinstackcapital.dropdetail'),
        ),
        migrations.AddField(
            model_name='myuser',
            name='referral',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coinstackcapital.referral'),
        ),
        migrations.AddField(
            model_name='myuser',
            name='logs',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coinstackcapital.requestlog'),
        ),
        migrations.AddField(
            model_name='myuser',
            name='security_setting',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coinstackcapital.security_settings'),
        ),
    ]
