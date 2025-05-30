# Generated by Django 5.1.1 on 2025-04-01 20:29

import django.core.validators
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GameHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('moves_taken', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('time_taken', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('was_best_time', models.BooleanField(default=False)),
                ('was_best_moves', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Game histories',
                'ordering': ['-completed_at'],
            },
        ),
        migrations.CreateModel(
            name='PuzzleRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_id', models.CharField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('state', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('invite_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('invite_used', models.BooleanField(default=False)),
                ('best_time', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('best_moves', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('games_completed', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('total_moves_made', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('current_move_count', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('last_played', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-last_played'],
            },
        ),
    ]
