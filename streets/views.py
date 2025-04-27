import numpy as np
from django.shortcuts import render
from django.http import HttpResponse
import osmnx as ox
from django.contrib.gis.geos import LineString
from django.contrib.gis.geos import Point

from streets.models import GeoAreaMapping, EdgeNode, City, Node, Edge

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import json
from django.db import transaction
from django.http import JsonResponse
from .models import Node, Edge
from django.http import JsonResponse
from .models import Node, Edge, EdgeNode
from django.http import JsonResponse
from .models import City, CityWalkabilityMetrics, CityBikeabilityMetrics


def db_map_view(request):
    return render(request, 'db_map.html')


def get_data(request):
    nodes = Node.objects.all()
    edges = Edge.objects.all()

    nodes_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [node.lon, node.lat]
                },
                "properties": {
                    "id": node.id,
                    "lat": node.lat,
                    "lon": node.lon
                }
            }
            for node in nodes
        ]
    }

    edges_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": json.loads(edge.geom.geojson),
                "properties": {
                    "id": edge.id
                }
            }
            for edge in edges
        ]
    }

    return JsonResponse({
        "nodes": nodes_geojson,
        "edges": edges_geojson
    })


def city_metrics_page(request):
    return render(request, 'city_metrics.html')


def get_city_metrics(request):
    city_name = request.GET.get('city_name')
    if not city_name:
        return JsonResponse({'error': 'City name is required.'}, status=400)

    try:
        city = City.objects.get(city_name__iexact=city_name)  #
    except City.DoesNotExist:
        return JsonResponse({'error': 'City not found.'}, status=404)

    try:
        walkability = CityWalkabilityMetrics.objects.get(city=city)
        bikeability = CityBikeabilityMetrics.objects.get(city=city)
    except (CityWalkabilityMetrics.DoesNotExist, CityBikeabilityMetrics.DoesNotExist):
        return JsonResponse({'error': 'Metrics data not found for this city.'}, status=404)

    data = {
        'city': city.city_name,
        'walkability_metrics': {
            'POP': walkability.POP,
            'CIR': walkability.CIR,
            'ORE': walkability.ORE,
            'RDE': walkability.RDE,
            'AST': walkability.AST,
            'ASL': walkability.ASL,
            'IND': walkability.IND,
            'WDR': walkability.WDR,
            'AWS': walkability.AWS,
            'ACO': walkability.ACO,
            'SCO': walkability.SCO,
        },
        'bikeability_metrics': {
            'POP': bikeability.POP,
            'CIR': bikeability.CIR,
            'ORE': bikeability.ORE,
            'RDE': bikeability.RDE,
            'AST': bikeability.AST,
            'ASL': bikeability.ASL,
            'IND': bikeability.IND,
            'BDR': bikeability.BDR,
            'ABS': bikeability.ABS,
            'ACO': bikeability.ACO,
            'SCO': bikeability.SCO,
        }
    }

    return JsonResponse(data)


def find_similar_cities(request):
    city_name = request.GET.get('city_name')
    top_n = int(request.GET.get('top_n', 5))

    city = City.objects.get(city_name=city_name)
    walk_metrics = CityWalkabilityMetrics.objects.get(city=city)
    bike_metrics = CityBikeabilityMetrics.objects.get(city=city)

    cities = City.objects.all()
    similar_cities = []

    for other_city in cities:
        if other_city == city:
            continue

        other_walk_metrics = CityWalkabilityMetrics.objects.get(city=other_city)
        other_bike_metrics = CityBikeabilityMetrics.objects.get(city=other_city)

        walk_vector = np.array([walk_metrics.POP, walk_metrics.CIR, walk_metrics.ORE, walk_metrics.RDE])
        bike_vector = np.array([bike_metrics.POP, bike_metrics.CIR, bike_metrics.ORE, bike_metrics.RDE])

        other_walk_vector = np.array([other_walk_metrics.POP, other_walk_metrics.CIR, other_walk_metrics.ORE, other_walk_metrics.RDE])
        other_bike_vector = np.array([other_bike_metrics.POP, other_bike_metrics.CIR, other_bike_metrics.ORE, other_bike_metrics.RDE])

        distance = np.linalg.norm(walk_vector - other_walk_vector) + np.linalg.norm(bike_vector - other_bike_vector)

        similar_cities.append({
            'city': other_city.city_name,
            'walkability_score': other_walk_metrics.AWS,
            'bikeability_score': other_bike_metrics.ABS,
            'similarity_score': 1 / (1 + distance)
        })

    similar_cities = sorted(similar_cities, key=lambda x: x['similarity_score'], reverse=True)[:top_n]

    return JsonResponse({'similar_cities': similar_cities})
