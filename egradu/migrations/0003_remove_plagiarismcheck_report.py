# Generated by Django 4.1.7 on 2023-03-14 18:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("egradu", "0002_documentcomments_commented_document"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="plagiarismcheck",
            name="report",
        ),
    ]