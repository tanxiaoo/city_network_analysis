import numpy as np
from django.shortcuts import render
from rest_framework import generics
import json
from .models import City, MetricValue, Metric, Node, Edge
from .serializers import MetricValueSerializer, MetricSerializer, CitySerializer, MetricValueCreateUpdateSerializer, \
    NodeSerializer, EdgeSerializer, NodeGeoJSONSerializer, EdgeGeoJSONSerializer
from rest_framework import viewsets
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.gis.geos import Polygon
from rest_framework.generics import ListAPIView
from .models import Node, Edge, City
from .serializers import NodeGeoJSONSerializer, EdgeGeoJSONSerializer
from django.shortcuts import get_object_or_404
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Node
from .serializers import NodeSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters


def db_map_view(request):
    return render(request, 'db_map.html')


def city_metrics_page(request):
    return render(request, 'city_metrics.html')


class MetricValueViewSet(viewsets.ModelViewSet):
    queryset = MetricValue.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MetricValueCreateUpdateSerializer
        return MetricValueSerializer

    def get_queryset(self):
        city_name = self.request.query_params.get('city_name', None)
        metric_name = self.request.query_params.get('metric_name', None)
        metric_type = self.request.query_params.get('metric_type', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        queryset = MetricValue.objects.all()

        if city_name:
            queryset = queryset.filter(city__name__iexact=city_name)
        if metric_name:
            queryset = queryset.filter(metric__name__iexact=metric_name)
        if metric_type:
            queryset = queryset.filter(metric__type=metric_type)
        if start_date:
            queryset = queryset.filter(datetime__gte=start_date)
        if end_date:
            queryset = queryset.filter(datetime__lte=end_date)

        return queryset

    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MetricViewSet(viewsets.ModelViewSet):
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ['name', 'type']

    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ['name']

    @action(detail=False, methods=['delete'], url_path='delete_graph')
    def delete_graph(self, request):
        city_name = request.query_params.get('city', None)

        if city_name:
            city = City.objects.filter(name=city_name).first()

            if not city:
                return Response({"error": f"City '{city_name}' not found."}, status=status.HTTP_404_NOT_FOUND)

            deleted_count, _ = Node.objects.filter(city=city).delete()
            return Response({
                "message": f"Deleted {deleted_count} node(s) (and associated edges) for city '{city_name}'."
            }, status=status.HTTP_200_OK)

        else:
            deleted_count, _ = Node.objects.all().delete()
            return Response({
                "message": f"Deleted {deleted_count} node(s) (and associated edges) from the entire database."
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='delete_metric_value')
    def delete_metric_value(self, request):
        city_name = request.query_params.get('city', None)

        if city_name:
            city = City.objects.filter(name=city_name).first()

            if not city:
                return Response({"error": f"City '{city_name}' not found."}, status=status.HTTP_404_NOT_FOUND)

            deleted_count, _ = MetricValue.objects.filter(city=city).delete()
            return Response({
                "message": f"Deleted {deleted_count} MetricValue(s) for city '{city_name}'."
            }, status=status.HTTP_200_OK)

        else:
            deleted_count, _ = MetricValue.objects.all().delete()
            return Response({
                "message": f"Deleted {deleted_count} MetricValue(s) from the entire database."
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    def get_queryset(self):
        city_id = self.request.query_params.get('city', None)
        queryset = Node.objects.all()

        if city_id:
            queryset = queryset.filter(city_id=city_id)

        return queryset

    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EdgeViewSet(viewsets.ModelViewSet):
    queryset = Edge.objects.all()
    serializer_class = EdgeSerializer

    def get_queryset(self):
        city_id = self.request.query_params.get('city', None)
        queryset = Edge.objects.all()

        if city_id:
            queryset = queryset.filter(city_id=city_id)

        return queryset

    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NodeGeoJSONView(generics.ListAPIView):
    serializer_class = NodeGeoJSONSerializer

    def get_queryset(self):
        queryset = Node.objects.all()

        city_name = self.request.query_params.get('city', None)
        if city_name:
            city = get_object_or_404(City, name=city_name)
            queryset = queryset.filter(city=city)

        bbox = self.request.query_params.get('bbox', None)
        if bbox:
            lng1, lat1, lng2, lat2 = map(float, bbox.split(','))
            polygon = Polygon.from_bbox((lng1, lat1, lng2, lat2))
            queryset = queryset.filter(geom__within=polygon)

        return queryset


class EdgeGeoJSONView(generics.ListAPIView):
    serializer_class = EdgeGeoJSONSerializer

    def get_queryset(self):
        queryset = Edge.objects.all()
        city_name = self.request.query_params.get('city', None)
        if city_name:
            city = get_object_or_404(City, name=city_name)
            queryset = queryset.filter(city=city)

        bbox = self.request.query_params.get('bbox', None)
        if bbox:
            lng1, lat1, lng2, lat2 = map(float, bbox.split(','))
            polygon = Polygon.from_bbox((lng1, lat1, lng2, lat2))
            queryset = queryset.filter(geom__within=polygon)

        return queryset

