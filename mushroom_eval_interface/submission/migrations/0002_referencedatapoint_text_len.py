# Generated by Django 5.0.6 on 2024-11-04 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submission', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='referencedatapoint',
            name='text_len',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
