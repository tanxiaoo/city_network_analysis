from django.db import migrations

def update_geom_to_multipolygon(apps, schema_editor):
    from streets.models import City
    from django.contrib.gis.geos import MultiPolygon, Polygon

    cities = City.objects.all()
    for city in cities:
        if isinstance(city.geom, Polygon):
            city.geom = MultiPolygon(city.geom)
            city.save()

class Migration(migrations.Migration):

    dependencies = [
        ('streets', '0006_alter_city_geom'),  # 使用存在的迁移文件
    ]

    operations = [
        migrations.RunPython(update_geom_to_multipolygon),
    ]
