import osmnx as ox
from streets.models import City, GeoAreaMapping, Node
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.contrib.gis.geos import GEOSGeometry
import shapely.geometry
from django.contrib.gis.geos import Point
from streets.models import City, CityWalkabilityMetrics, CityBikeabilityMetrics
import osmnx as ox
import shapely
from django.contrib.gis.geos import GEOSGeometry


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
    {"city_name": "Buenos Aires", "place_name": "Buenos Aires, Argentina", "country": "Argentina", "geo_area": "SA",
     "built_up_area_km2": 673.0},
    {"city_name": "Bogota", "place_name": "Bogotá, Colombia", "country": "Colombia", "geo_area": "SA",
     "built_up_area_km2": 152.0},
    {"city_name": "Chicago", "place_name": "Chicago, USA", "country": "USA", "geo_area": "NA",
     "built_up_area_km2": 524.0},
    {"city_name": "Ottawa", "place_name": "Ottawa, Canada", "country": "Canada", "geo_area": "NA",
     "built_up_area_km2": 39.6},
    {"city_name": "Panama", "place_name": "Panama, Panama", "country": "Panama", "geo_area": "CA",
     "built_up_area_km2": 62.0},
    {"city_name": "Havana", "place_name": "Havana, Cuba", "country": "Cuba", "geo_area": "CA",
     "built_up_area_km2": 56.1},
    {"city_name": "Milan", "place_name": "Milan, Italy", "country": "Italy", "geo_area": "EU",
     "built_up_area_km2": 176.4},
    {"city_name": "Athens", "place_name": "Athens, Greece", "country": "Greece", "geo_area": "EU",
     "built_up_area_km2": 115.2},
    {"city_name": "Shanghai", "place_name": "Shanghai, China", "country": "China", "geo_area": "AS",
     "built_up_area_km2": 718.0},
    {"city_name": "Hanoi", "place_name": "Hanoi, Vietnam", "country": "Vietnam", "geo_area": "AS",
     "built_up_area_km2": 161.9},
    {"city_name": "Dubai", "place_name": "Dubai, UAE", "country": "UAE", "geo_area": "ME",
     "built_up_area_km2": 197.8},
    {"city_name": "Doha", "place_name": "Doha, Qatar", "country": "Qatar", "geo_area": "ME",
     "built_up_area_km2": 107.8},
    {"city_name": "Wellington", "place_name": "Wellington, New Zealand", "country": "New Zealand", "geo_area": "OC",
     "built_up_area_km2": 13.9},
    {"city_name": "Port Moresby", "place_name": "Port Moresby, Papua New Guinea", "country": "Papua New Guinea",
     "geo_area": "OC", "built_up_area_km2": 8.4},
    {"city_name": "Lagos", "place_name": "Lagos, Nigeria", "country": "Nigeria", "geo_area": "AF",
     "built_up_area_km2": 415.9},
    {"city_name": "Alexandria", "place_name": "Alexandria, Egypt", "country": "Egypt", "geo_area": "AF",
     "built_up_area_km2": 81.7},
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

        except TypeError as e:
            print(f"Error geocoding {info['city_name']}: {e}")
            boundary_geom_django = None
            area_km2 = info["built_up_area_km2"]

        City.objects.get_or_create(
            city_name=info["city_name"],
            defaults={
                "country": info["country"],
                "geo_area": geo_area,
                "area_km2": area_km2,
                "built_up_area_km2": info["built_up_area_km2"],
                "geom": boundary_geom_django,
            }
        )

        print(f"City {City.city_name} has been saved to the database.")


walkability_data = [
    {"city_name": "Buenos Aires", "POP": 14179912, "CIR": 1.018, "ORE": 3.286, "RDE": 51368, "AST": 0.028, "ASL": 86.345, "IND": 326.446, "WDR": 0.771, "AWS": 3.429, "ACO": 8.005, "SCO": 10.826},
    {"city_name": "Bogota", "POP": 10419360, "CIR": 1.047, "ORE": 3.552, "RDE": 79835, "AST": 0.048, "ASL": 50.608, "IND": 877.276, "WDR": 1.405, "AWS": 3.863, "ACO": 9.242, "SCO": 15.193},
    {"city_name": "Chicago", "POP": 5318734, "CIR": 1.059, "ORE": 2.457, "RDE": 94108, "AST": 0.026, "ASL": 54.389, "IND": 929.989, "WDR": 3.579, "AWS": 3.830, "ACO": 29.217, "SCO": 59.412},
    {"city_name": "Ottawa", "POP": 604618, "CIR": 1.062, "ORE": 3.366, "RDE": 144617, "AST": 0.033, "ASL": 41.004, "IND": 1936.544, "WDR": 5.263, "AWS": 3.594, "ACO": 18.898, "SCO": 29.599},
    {"city_name": "Panama", "POP": 1612439, "CIR": 1.080, "ORE": 3.569, "RDE": 57909, "AST": 0.046, "ASL": 72.213, "IND": 431.537, "WDR": 1.032, "AWS": 3.482, "ACO": 7.029, "SCO": 10.316},
    {"city_name": "Havana", "POP": 1632771, "CIR": 1.049, "ORE": 3.555, "RDE": 72756, "AST": 0.032, "ASL": 77.953, "IND": 510.156, "WDR": 1.058, "AWS": 3.111, "ACO": 6.534, "SCO": 8.540},
    {"city_name": "Milan", "POP": 3135553, "CIR": 1.068, "ORE": 3.544, "RDE": 84354, "AST": 0.035, "ASL": 49.257, "IND": 959.704, "WDR": 2.576, "AWS": 3.805, "ACO": 12.988, "SCO": 23.377},
    {"city_name": "Athens", "POP": 3166757, "CIR": 1.031, "ORE": 3.550, "RDE": 86771, "AST": 0.060, "ASL": 56.686, "IND": 875.439, "WDR": 1.086, "AWS": 3.519, "ACO": 7.072, "SCO": 10.051},
    {"city_name": "Shanghai", "POP": 30678616, "CIR": 1.049, "ORE": 3.424, "RDE": 33536, "AST": 0.027, "ASL": 157.808, "IND": 115.765, "WDR": 1.184, "AWS": 3.140, "ACO": 173.804, "SCO": 251.134},
    {"city_name": "Hanoi", "POP": 4965520, "CIR": 1.059, "ORE": 3.574, "RDE": 88463, "AST": 0.029, "ASL": 65.535, "IND": 754.677, "WDR": 1.288, "AWS": 3.573, "ACO": 7.804, "SCO": 12.690},
    {"city_name": "Dubai", "POP": 4565477, "CIR": 1.068, "ORE": 3.467, "RDE": 77426, "AST": 0.063, "ASL": 56.313, "IND": 807.691, "WDR": 1.985, "AWS": 3.548, "ACO": 12.381, "SCO": 26.379},
    {"city_name": "Doha", "POP": 1980416, "CIR": 1.079, "ORE": 3.452, "RDE": 61697, "AST": 0.031, "ASL": 66.596, "IND": 541.642, "WDR": 1.143, "AWS": 3.586, "ACO": 6.367, "SCO": 8.934},
    {"city_name": "Wellington", "POP": 154120, "CIR": 1.120, "ORE": 3.523, "RDE": 67009, "AST": 0.078, "ASL": 52.959, "IND": 676.056, "WDR": 3.139, "AWS": 3.278, "ACO": 6.140, "SCO": 11.008},
    {"city_name": "Port Moresby", "POP": 442164, "CIR": 1.119, "ORE": 3.569, "RDE": 72745, "AST": 0.046, "ASL": 109.971, "IND": 355.963, "WDR": 1.023, "AWS": 2.947, "ACO": 4.267, "SCO": 4.417},
    {"city_name": "Lagos", "POP": 12846045, "CIR": 1.055, "ORE": 3.556, "RDE": 34911, "AST": 0.030, "ASL": 100.951, "IND": 196.758, "WDR": 0.635, "AWS": 3.635, "ACO": 6.058, "SCO": 9.316},
    {"city_name": "Alexandria", "POP": 6931368, "CIR": 1.032, "ORE": 3.458, "RDE": 74548, "AST": 0.048, "ASL": 59.070, "IND": 744.167, "WDR": 0.648, "AWS": 3.724, "ACO": 7.081, "SCO": 12.288},
]


def save_walkability_metrics():
    for data in walkability_data:
        city_name = data["city_name"]
        data_without_city = {k: v for k, v in data.items() if k not in ['city', 'city_name']}
        try:
            city = City.objects.get(city_name=city_name)

            CityWalkabilityMetrics.objects.update_or_create(
                city=city,
                defaults=data_without_city,
            )

            print(f"Walkability metrics for {city_name} saved successfully.")

        except City.DoesNotExist:
            print(f"City '{city_name}' not found in the database. Skipping.")


bikeability_data = [
    {"city_name": "Buenos Aires", "POP": 14179912, "CIR": 1.015, "ORE": 3.203, "RDE": 49065, "AST": 0.024, "ASL": 98.394, "IND": 270.367, "BDR": 0.647, "ABS": 3.748, "ACO": 8.470, "SCO": 12.275},
    {"city_name": "Bogota", "POP": 10419360, "CIR": 1.048, "ORE": 3.551, "RDE": 61504, "AST": 0.044, "ASL": 68.100, "IND": 489.618, "BDR": 0.804, "ABS": 3.404, "ACO": 13.838, "SCO": 30.991},
    {"city_name": "Chicago", "POP": 5318734, "CIR": 1.068, "ORE": 2.584, "RDE": 66791, "AST": 0.022, "ASL": 75.839, "IND": 453.967, "BDR": 1.822, "ABS": 3.753, "ACO": 6.686, "SCO": 14.144},
    {"city_name": "Ottawa", "POP": 604618, "CIR": 1.072, "ORE": 3.377, "RDE": 82081, "AST": 0.029, "ASL": 64.928, "IND": 586.625, "BDR": 1.886, "ABS": 3.598, "ACO": 8.877, "SCO": 16.510},
    {"city_name": "Panama", "POP": 1612439, "CIR": 1.072, "ORE": 3.567, "RDE": 51913, "AST": 0.044, "ASL": 80.275, "IND": 335.305, "BDR": 0.832, "ABS": 3.300, "ACO": 8.974, "SCO": 15.316},
    {"city_name": "Havana", "POP": 1632771, "CIR": 1.047, "ORE": 3.558, "RDE": 64816, "AST": 0.030, "ASL": 92.278, "IND": 378.058, "BDR": 0.796, "ABS": 3.604, "ACO": 6.335, "SCO": 9.373},
    {"city_name": "Milan", "POP": 3135553, "CIR": 1.061, "ORE": 3.526, "RDE": 61513, "AST": 0.029, "ASL": 70.245, "IND": 461.082, "BDR": 1.317, "ABS": 3.670, "ACO": 51.332, "SCO": 86.602},
    {"city_name": "Athens", "POP": 3166757, "CIR": 1.028, "ORE": 3.546, "RDE": 79947, "AST": 0.055, "ASL": 64.170, "IND": 701.697, "BDR": 0.884, "ABS": 3.070, "ACO": 7.769, "SCO": 13.745},
    {"city_name": "Shanghai", "POP": 30678616, "CIR": 1.047, "ORE": 3.403, "RDE": 32356, "AST": 0.024, "ASL": 176.601, "IND": 98.481, "BDR": 1.021, "ABS": 3.724, "ACO": 78.621, "SCO": 128.654},
    {"city_name": "Hanoi", "POP": 4965520, "CIR": 1.056, "ORE": 3.577, "RDE": 80389, "AST": 0.026, "ASL": 74.563, "IND": 602.049, "BDR": 1.029, "ABS": 3.647, "ACO": 8.199, "SCO": 14.826},
    {"city_name": "Dubai", "POP": 4565477, "CIR": 1.070, "ORE": 3.454, "RDE": 66863, "AST": 0.059, "ASL": 70.321, "IND": 547.156, "BDR": 1.373, "ABS": 3.195, "ACO": 50.727, "SCO": 95.572},
    {"city_name": "Doha", "POP": 1980416, "CIR": 1.077, "ORE": 3.440, "RDE": 63745, "AST": 0.030, "ASL": 77.212, "IND": 473.217, "BDR": 1.018, "ABS": 3.579, "ACO": 53.867, "SCO": 87.018},
    {"city_name": "Wellington", "POP": 154120, "CIR": 1.112, "ORE": 3.514, "RDE": 52335, "AST": 0.069, "ASL": 61.568, "IND": 417.051, "BDR": 2.109, "ABS": 2.901, "ACO": 4.219, "SCO": 6.099},
    {"city_name": "Port Moresby", "POP": 442164, "CIR": 1.112, "ORE": 3.569, "RDE": 70391, "AST": 0.047, "ASL": 111.711, "IND": 334.182, "BDR": 0.974, "ABS": 2.246, "ACO": 4.344, "SCO": 4.416},
    {"city_name": "Lagos", "POP": 12846045, "CIR": 1.054, "ORE": 3.556, "RDE": 34729, "AST": 0.030, "ASL": 101.862, "IND": 193.692, "BDR": 0.626, "ABS": 3.590, "ACO": 6.605, "SCO": 8.622},
    {"city_name": "Alexandria", "POP": 6931368, "CIR": 1.032, "ORE": 3.449, "RDE": 73675, "AST": 0.046, "ASL": 62.419, "IND": 694.789, "BDR": 0.606, "ABS": 2.966, "ACO": 8.266, "SCO": 16.057}
]


def save_bikeability_metrics():
    for data in bikeability_data:
        city_name = data["city_name"]
        data_without_city = {k: v for k, v in data.items() if k not in ['city', 'city_name']}
        try:
            city = City.objects.get(city_name=city_name)

            CityBikeabilityMetrics.objects.update_or_create(
                city=city,
                defaults=data_without_city,
            )

            print(f"Bikeability metrics for {city_name} saved successfully.")

        except City.DoesNotExist:
            print(f"City '{city_name}' not found in the database. Skipping.")

