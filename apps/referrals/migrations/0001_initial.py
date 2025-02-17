# Generated by Django 4.2.6 on 2025-02-16 08:35

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReferralCode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral_codes', to='authentication.user')),
            ],
            options={
                'db_table': 'referral_codes',
            },
        ),
        migrations.CreateModel(
            name='Referral',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('referral_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='referrals.referralcode')),
                ('referred', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referrals_received', to='authentication.user')),
                ('referrer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referrals_given', to='authentication.user')),
            ],
            options={
                'db_table': 'referrals',
            },
        ),
    ]
