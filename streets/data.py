import osmnx as ox
from streets.models import City, GeoAreaMapping, Metric, MetricValue
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.contrib.gis.geos import GEOSGeometry
import shapely.geometry
from django.contrib.gis.geos import Point
from streets.models import City
import osmnx as ox
import shapely
from django.contrib.gis.geos import GEOSGeometry
from datetime import datetime


geo_area_data = [
    {'geo_area': 'SA', 'full_name': 'South America'},
    {'geo_area': 'NA', 'full_name': 'North America'},
    {'geo_area': 'CA', 'full_name': 'Central America'},
    {'geo_area': 'EU', 'full_name': 'Europe'},
    {'geo_area': 'AS', 'full_name': 'Asia'},
    {'geo_area': 'ME', 'full_name': 'Middle East'},
    {'geo_area': 'OC', 'full_name': 'Oceania'},
    {'geo_area': 'AF', 'full_name': 'Africa'}
]


def save_geo_area():
    for data in geo_area_data:
        GeoAreaMapping.objects.update_or_create(
            geo_area=data['geo_area'],
            defaults={'full_name': data['full_name']}
        )
    print("GeoAreaMapping data inserted or updated successfully!")


city_info = [
    {"name": "Bucharest", "place_name": "Bucharest, Romania", "country": "Romania", "geo_area": "EU", "built_up_area_km2": 228.0, "population": 1821000},
    {"name": "Amsterdam", "place_name": "Amsterdam, Netherlands", "country": "Netherlands", "geo_area": "EU", "built_up_area_km2": 219.0, "population": 905000},
    {"name": "Kinshasa", "place_name": "Kinshasa, Congo", "country": "Congo", "geo_area": "AF", "built_up_area_km2": 308.5, "population": 15150000},
    {"name": "Kampala", "place_name": "Kampala, Uganda", "country": "Uganda", "geo_area": "AF", "built_up_area_km2": 111.3, "population": 1650000},
    {"name": "Gaborone", "place_name": "Gaborone, Botswana", "country": "Botswana", "geo_area": "AF", "built_up_area_km2": 64.0, "population": 270000},
    {"name": "Brasilia", "place_name": "Brasilia, Brazil", "country": "Brazil", "geo_area": "SA", "built_up_area_km2": 230.0, "population": 3100000},
    {"name": "Sucre", "place_name": "Sucre, Bolivia", "country": "Bolivia", "geo_area": "SA", "built_up_area_km2": 45.2, "population": 390000},
    {"name": "Tbilisi", "place_name": "Tbilisi, Georgia", "country": "Georgia", "geo_area": "AS", "built_up_area_km2": 140.5, "population": 1150000},
    {"name": "Teheran", "place_name": "Teheran, Iran", "country": "Iran", "geo_area": "AS", "built_up_area_km2": 370.0, "population": 9000000},
    {"name": "Astana", "place_name": "Astana, Kazakhstan", "country": "Kazakhstan", "geo_area": "AS", "built_up_area_km2": 105.0, "population": 1300000},
]


def create_city():
    for info in city_info:
        geo_area = GeoAreaMapping.objects.get(geo_area=info["geo_area"])
        try:
            city_boundary = ox.geocode_to_gdf(info["place_name"])

            if city_boundary.empty or city_boundary.geometry.isnull().all():
                boundary_geom_django = None
                area_km2 = info["built_up_area_km2"]
            else:
                boundary_geom = city_boundary.geometry.iloc[0]
                if isinstance(boundary_geom, (Polygon, MultiPolygon)):
                    boundary_geom_django = GEOSGeometry(boundary_geom.wkt)
                    if isinstance(boundary_geom, Polygon):
                        boundary_geom_django = MultiPolygon([boundary_geom_django])
                    area_km2 = boundary_geom_django.area / 1e6
                else:
                    boundary_geom_django = None
                    area_km2 = info["built_up_area_km2"]

        except Exception as e:
            print(f"Error geocoding {info['name']}: {e}")
            boundary_geom_django = None
            area_km2 = info["built_up_area_km2"]

        city_obj, created = City.objects.get_or_create(
            name=info["name"],
            defaults={
                "country": info["country"],
                "geo_area": geo_area,
                "population": info["population"],
                "area_km2": area_km2,
                "built_up_area_km2": info["built_up_area_km2"],
                "geom": boundary_geom_django,
            }
        )

        print(f"City {city_obj.name} has been {'created' if created else 'skipped'} in the database.")


metric_data = {
    "CIR": "Circuity",
    "ORE": "Orientation Entropy",
    "RDE": "Road Density",
    "AST": "Average Steepness",
    "ASL": "Average Street Length",
    "IND": "Intersection Density"
}


def save_metric():
    types = ["walk", "bike"]

    for name in metric_data.keys():
        for metric_type in types:
            Metric.objects.get_or_create(name=name, type=metric_type)


def save_milan_metric_values():
    city = City.objects.get(city_name="Milan")
    test_date = datetime(2025, 4, 30, 10, 0, 0)

    for name in metric_data.keys():
        for metric_type in ["walk", "bike"]:
            metric = Metric.objects.get(name=name, type=metric_type)
            value = round(1.0 + hash(f"{name}-{metric_type}") % 200 / 100, 2)  # 简单生成一个浮点数

            MetricValue.objects.get_or_create(
                metric=metric,
                city=city,
                datetime=test_date,
                defaults={"value": value}
            )