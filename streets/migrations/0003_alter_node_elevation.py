# Generated by Django 5.1.7 on 2025-05-04 07:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("streets", "0002_node_edge"),
    ]

    operations = [
        migrations.AlterField(
            model_name="node",
            name="elevation",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
