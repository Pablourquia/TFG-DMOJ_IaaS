# Generated by Django 3.2.25 on 2024-04-18 19:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0147_auto_20240418_1837'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question',
            old_name='type',
            new_name='type_question',
        ),
    ]
