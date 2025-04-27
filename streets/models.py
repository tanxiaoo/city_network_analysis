from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon


class GeoAreaMapping(models.Model):
    geo_area = models.CharField(max_length=2, primary_key=True)
    full_name = models.CharField(max_length=255)

    def __str__(self):
        return self.full_name


# Create your models here.
class City(models.Model):
    city_name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    geo_area = models.ForeignKey(GeoAreaMapping, on_delete=models.CASCADE)
    area_km2 = models.FloatField()
    built_up_area_km2 = models.FloatField()
    geom = models.MultiPolygonField(null=True, blank=True, default=MultiPolygon())

    def __str__(self):
        return self.city_name


class Node(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    lat = models.FloatField()
    lon = models.FloatField()
    elevation = models.FloatField()
    geom = models.PointField(srid=4326)

    def __str__(self):
        return f"Node {self.id} in  {self.city.city_name}"


class Edge(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    name = models.CharField(max_length=255)
    is_pedestrian = models.BooleanField(default=False)
    is_cycling = models.BooleanField(default=False)
    is_driving = models.BooleanField(default=False)
    speed_limit = models.IntegerField(null=True, blank=True)
    street_type = models.CharField(max_length=255, null=True, blank=True)
    geom = models.LineStringField(srid=4326)

    def __str__(self):
        return self.name


class EdgeNode(models.Model):
    edge = models.ForeignKey(Edge, on_delete=models.CASCADE, verbose_name="Edge")
    node = models.ForeignKey(Node, on_delete=models.CASCADE, verbose_name="Node")
    position = models.IntegerField()

    def __str__(self):
        return f"StreetNode {self.id} in street {self.edge.name}"


class CityWalkabilityMetrics(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    POP = models.IntegerField()
    CIR = models.FloatField()
    ORE = models.FloatField()
    RDE = models.FloatField()
    AST = models.FloatField()
    ASL = models.FloatField()
    IND = models.FloatField()
    WDR = models.FloatField()  # Walking Driving Ratio
    AWS = models.FloatField()  # Average Walking Score
    ACO = models.FloatField()  # Accessibility Score
    SCO = models.FloatField()  # Street Connectivity Score

    class Meta:
        unique_together = ('city',)

    def __str__(self):
        return f"{self.city.city_name} Walkability Metrics"


class CityBikeabilityMetrics(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    POP = models.IntegerField()
    CIR = models.FloatField()
    ORE = models.FloatField()
    RDE = models.FloatField()
    AST = models.FloatField()
    ASL = models.FloatField()
    IND = models.FloatField()
    BDR = models.FloatField()  # Biking Driving Ratio
    ABS = models.FloatField()  # Average Biking Score
    ACO = models.FloatField()  # Accessibility Score
    SCO = models.FloatField()  # Street Connectivity Score

    class Meta:
        unique_together = ('city',)

    def __str__(self):
        return f"{self.city.city_name} Bikeability Metrics"
