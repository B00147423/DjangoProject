# Generated by Django 4.2.16 on 2024-11-13 23:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jigsaw_puzzle', '0005_alter_jigsawpuzzlepiece_x_position_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jigsawpuzzlepiece',
            name='x_position',
        ),
        migrations.RemoveField(
            model_name='jigsawpuzzlepiece',
            name='y_position',
        ),
        migrations.AddField(
            model_name='jigsawpuzzlepiece',
            name='player1_x_position',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='jigsawpuzzlepiece',
            name='player1_y_position',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='jigsawpuzzlepiece',
            name='player2_x_position',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='jigsawpuzzlepiece',
            name='player2_y_position',
            field=models.IntegerField(default=-1),
        ),
        migrations.AlterField(
            model_name='jigsawpuzzlepiece',
            name='image_piece',
            field=models.ImageField(upload_to='pieces/'),
        ),
    ]
