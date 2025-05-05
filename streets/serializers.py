from rest_framework import serializers
from .models import MetricValue, Metric, City, Node, Edge


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
    city = CitySimplifiedSerializer()
    metric = MetricSimplifiedSerializer()

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
