# Generated by Django 5.1.1 on 2024-09-23 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('puzzles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='puzzle',
            name='name',
            field=models.CharField(default='puzzleRoomNameDefault', max_length=100),
            preserve_default=False,
        ),
    ]