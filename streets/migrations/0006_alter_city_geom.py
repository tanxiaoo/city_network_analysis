from django.db import migrations
from django.contrib.gis.db import models

class Migration(migrations.Migration):

    dependencies = [
        ('streets', '0005_citybikeabilitymetrics_citywalkabilitymetrics_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='city',
            name='geom',
            field=models.MultiPolygonField(null=True, blank=True),
        ),
    ]

