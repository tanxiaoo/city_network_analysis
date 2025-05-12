from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon


class GeoAreaMapping(models.Model):
    geo_area = models.CharField(max_length=2, primary_key=True)
    full_name = models.CharField(max_length=255)

    def __str__(self):
        return self.full_name


# Create your models here.
class City(models.Model):
    name = models.CharField(max_length=255, unique=True)
    country = models.CharField(max_length=255)
    geo_area = models.ForeignKey(GeoAreaMapping, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Metric(models.Model):
    METRICS_TYPES = [
        ("walk","Walkability"),
        ("bike","Bikeability")
    ]

    name = models.CharField(max_length=50)
    type = models.CharField(max_length=10, choices=METRICS_TYPES)

    class Meta:
        unique_together = ('name', 'type')

    def __str__(self):
        return f"{self.type} - {self.name}"


class MetricValue(models.Model):
    metric = models.ForeignKey(Metric, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    value = models.FloatField()
    datetime = models.DateTimeField()

    class Meta:
        unique_together = ('metric', 'city', 'datetime')

    def __str__(self):
        return f"{self.city.name} - {self.metric.name} at {self.datetime}"


class Node(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    osm_id = models.BigIntegerField(primary_key=True)
    geom = models.PointField(srid=4326,geography=True)

    def __str__(self):
        return f"Node {self.id} in  {self.city.name}"


class Edge(models.Model):
    city = models.ForeignKey('City', on_delete=models.CASCADE, verbose_name="City")
    start_node = models.ForeignKey('Node', on_delete=models.CASCADE, related_name='start_edges')
    end_node = models.ForeignKey('Node', on_delete=models.CASCADE, related_name='end_edges')
    geom = models.LineStringField(srid=4326, geography=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['city', 'start_node', 'end_node'], name='unique_edge_in_city')
        ]
        indexes = [
            models.Index(fields=['geom']),
        ]

    def __str__(self):
        return f"Edge {self.id} in {self.city.name}: {self.start_node.id} → {self.end_node.id}"


#
# class Node(models.Model):
#     city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
#     osm_id = models.BigIntegerField(null=True, blank=True, unique=True)
#     elevation = models.FloatField(null=True, blank=True)
#     geom = models.PointField(srid=4326, geography=True)
#
#     def __str__(self):
#         return f"Node {self.id} in  {self.city.name}"


# class Edge(models.Model):
#     city = models.ForeignKey('City', on_delete=models.CASCADE, verbose_name="City")
#     start_node = models.ForeignKey('Node', on_delete=models.CASCADE, related_name='start_edges')
#     end_node = models.ForeignKey('Node', on_delete=models.CASCADE, related_name='end_edges')
#     geom = models.LineStringField(srid=4326, geography=True)
#     data = models.JSONField(null=True, blank=True)
#
#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['city', 'start_node', 'end_node'], name='unique_edge_in_city')
#         ]
#         indexes = [
#             models.Index(fields=['geom']),
#         ]
#
#     def __str__(self):
#         return f"Edge {self.id} in {self.city.name}: {self.start_node.id} → {self.end_node.id}"
#
#     def set_data(self, name=None, length=None, mode=None, speed_limit=None, edge_type=None):
#         valid_modes = ['pedestrian', 'driving', 'cycling', 'public_transport']
#         valid_edge_types = ['highway', 'urban', 'rural', 'alley']
#
#         if length is not None and not isinstance(length, (int, float)):
#             raise ValueError("Length must be an integer or float.")
#         if speed_limit is not None and not isinstance(speed_limit, (int, float)):
#             raise ValueError("Speed limit must be an integer or float.")
#
#         self.data = {
#             'name': name,
#             'length': length,
#             'mode': mode if mode in valid_modes else None,
#             'speed_limit': speed_limit,
#             'edge_type': edge_type if edge_type in valid_edge_types else None
#         }
#         self.save()



