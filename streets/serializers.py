from rest_framework import serializers
from .models import MetricValue, Metric, City, Node, Edge
from rest_framework_gis.serializers import GeoFeatureModelSerializer


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'


class CitySimplifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['name']


class MetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = '__all__'


class MetricSimplifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = ['name', 'type']


class MetricValueSerializer(serializers.ModelSerializer):
    metric = serializers.PrimaryKeyRelatedField(queryset=Metric.objects.all())
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())

    class Meta:
        model = MetricValue
        fields = '__all__'


class MetricValueCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricValue
        fields = '__all__'


class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = '__all__'


class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = '__all__'


class NodeGeoJSONSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Node
        geo_field = 'geom'
        fields = []


class EdgeGeoJSONSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Edge
        geo_field = 'geom'
        fields = []
