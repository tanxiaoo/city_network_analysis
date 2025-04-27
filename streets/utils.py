import json
import osmnx as ox
from django.contrib.gis.geos import Point
from django.contrib.gis.geos import LineString
from streets.models import City, CityWalkabilityMetrics, CityBikeabilityMetrics
import math
from django.db.models import Count
from .models import Edge, City, Node, EdgeNode


def fetch_data(city_name: str, country: str, modality: str = "drive"):
    place_name = f"{city_name}, {country}"
    print(f"Fetching network for {place_name} with modality: {modality}")

    graph = ox.graph_from_place(place_name, network_type=modality)
    graph = ox.project_graph(graph, to_crs="EPSG:4326")

    edges_gdf = ox.graph_to_gdfs(graph, nodes=False, edges=True).iloc[90:100]
    nodes_ids = set()
    for (u, v, _) in edges_gdf.index:
        nodes_ids.add(u)
        nodes_ids.add(v)
    nodes_gdf = ox.graph_to_gdfs(graph, nodes=True, edges=False).loc[list(nodes_ids)]

    return edges_gdf, nodes_gdf


def save_edges(city_name: str, edges_gdf, modality: str = "drive"):
    edges_geojson = json.loads(edges_gdf.to_json())
    city = City.objects.get(city_name=city_name)

    for feature in edges_geojson['features']:
        edge_id = feature['id']
        name = feature['properties'].get('name', 'Unnamed Street')
        coordinates = feature['geometry']['coordinates']
        highway_type = feature['properties'].get('highway', '')
        maxspeed = feature['properties'].get('maxspeed')
        speed_limit = int(maxspeed[0]) if isinstance(maxspeed, list) and maxspeed else int(maxspeed) if isinstance(maxspeed, str) else None

        if isinstance(highway_type, list):
            highway_type = set(highway_type)
        else:
            highway_type = {highway_type}

        street_type = 'unclassified' if not highway_type else next(iter(highway_type))
        is_pedestrian = any(t in highway_type for t in ["pedestrian", "footway", "steps", "path"])
        is_cycling = any(t in highway_type for t in ["cycleway", "living_street", "track"])
        is_driving = any(t in highway_type for t in [
            "primary", "secondary", "tertiary", "residential",
            "unclassified", "motorway", "trunk", "service", "road"])

        if modality == "drive":
            is_driving = True
        elif modality == "cycle":
            is_cycling = True
        elif modality == "walk":
            is_pedestrian = True

        geom = LineString([tuple(coord) for coord in coordinates])

        Edge.objects.update_or_create(
            id=edge_id,
            city=city,
            defaults={
                'name': name,
                "is_pedestrian": is_pedestrian,
                "is_cycling": is_cycling,
                "is_driving": is_driving,
                "speed_limit": speed_limit,
                "street_type": street_type,
                "geom": geom,
            }
        )

    print(f"Saved {len(edges_geojson['features'])} streets to the database.")


def save_nodes(city_name: str, nodes_gdf):
    nodes_geojson = json.loads(nodes_gdf.to_json())
    city = City.objects.get(city_name=city_name)

    for feature in nodes_geojson["features"]:
        props = feature["properties"]
        coord = feature["geometry"]["coordinates"]
        node_id = int(feature["id"])
        lat = props.get("y")
        lon = props.get("x")
        point = Point(lon, lat)

        Node.objects.create(
            id=node_id,
            city=city,
            lat=lat,
            lon=lon,
            elevation=0.0,
            geom=point,
        )

    print(f"Saved {len(nodes_geojson['features'])} nodes to the database.")


def save_edge_nodes(city_name: str, edges_gdf, nodes_gdf):
    edges_geojson = json.loads(edges_gdf.to_json())
    nodes_geojson = json.loads(nodes_gdf.to_json())
    city = City.objects.get(city_name=city_name)

    for edge_feature in edges_geojson['features']:
        edge_id = edge_feature['id']
        edge = Edge.objects.get(id=edge_id, city=city)

        coordinates = edge_feature['geometry']['coordinates']

        for position, coord in enumerate(coordinates):
            node_id = None
            for node_feature in nodes_geojson["features"]:
                node_coord = node_feature["geometry"]["coordinates"]
                if node_coord == coord:
                    node_id = int(node_feature["id"])
                    break

            if node_id:
                node = Node.objects.get(id=node_id, city=city)
                EdgeNode.objects.create(
                    edge=edge,
                    node=node,
                    position=position
                )

    print(f"Saved EdgeNode relationships to the database.")


def save_urban_metrics(city_name: str):
    city = City.objects.get(city_name=city_name)
    metrics = calculate_urban_metrics(city_name)

    # Save Walkability metrics
    CityWalkabilityMetrics.objects.update_or_create(
        city=city,
        defaults={
            'POP': 0,  # Placeholder value for POP
            'CIR': metrics.get('average_circuity', 0),
            'ORE': metrics.get('street_angle_entropy', 0),
            'RDE': metrics.get('road_density', 0),
            'AST': metrics.get('average_steepness', 0),
            'ASL': metrics.get('average_street_length', 0),
            'IND': metrics.get('intersection_density', 0),
            'WDR': metrics.get('walking_driving_ratio', 0),
            'AWS': metrics.get('average_walking_score', 0),
            'ACO': metrics.get('connectivity', 0),
            'SCO': metrics.get('connectivity', 0),
        }
    )
    print(f"Metrics for {city_name} (walkability) saved successfully.")

    # Save Bikeability metrics
    CityBikeabilityMetrics.objects.update_or_create(
        city=city,
        defaults={
            'POP': 0,  # Placeholder value for POP
            'CIR': metrics.get('average_circuity', 0),
            'ORE': metrics.get('street_angle_entropy', 0),
            'RDE': metrics.get('road_density', 0),
            'AST': metrics.get('average_steepness', 0),
            'ASL': metrics.get('average_street_length', 0),
            'IND': metrics.get('intersection_density', 0),
            'BDR': metrics.get('biking_driving_ratio', 0),
            'ABS': metrics.get('average_biking_score', 0),
            'ACO': metrics.get('connectivity', 0),
            'SCO': metrics.get('connectivity', 0),
        }
    )
    print(f"Metrics for {city_name} (bikeability) saved successfully.")


def calculate_urban_metrics(city_name: str):
    city = City.objects.get(city_name=city_name)

    # 1. Average Circuity
    total_circuity = 0
    count_circuity = 0
    for edge in Edge.objects.filter(city=city):
        nodes = EdgeNode.objects.filter(edge=edge)
        if nodes.count() == 2:
            node1, node2 = nodes[0].node, nodes[1].node
            straight_distance = calculate_distance(node1, node2)
            if straight_distance > 0:
                circuity = edge.geom.length / straight_distance
                total_circuity += circuity
                count_circuity += 1
    average_circuity = total_circuity / count_circuity if count_circuity > 0 else 0

    # 2. Orientation Entropy (Street Angle Distribution Entropy)
    street_angles = []
    for edge in Edge.objects.filter(city=city):
        geom = edge.geom
        angle = calculate_bearing(geom)
        street_angles.append(angle)
    angle_counts = [0] * 36
    for angle in street_angles:
        angle_index = int(angle // 10)
        angle_counts[angle_index] += 1
    total_angles = len(street_angles)
    entropy = -sum((count / total_angles) * math.log(count / total_angles) for count in angle_counts if count > 0)

    # 3. Road Density
    total_street_segments = Edge.objects.filter(city=city).count()
    road_density = total_street_segments / city.built_up_area_km2 if city.built_up_area_km2 > 0 else 0

    # 4. Average Steepness
    total_steepness = 0
    count_steepness = 0
    for edge in Edge.objects.filter(city=city):
        nodes = EdgeNode.objects.filter(edge=edge)
        if nodes.count() == 2:
            node1, node2 = nodes[0].node, nodes[1].node
            elevation_difference = abs(node1.elevation - node2.elevation)
            horizontal_distance = calculate_distance(node1, node2)
            if horizontal_distance > 0:
                steepness = elevation_difference / horizontal_distance
                total_steepness += steepness
                count_steepness += 1
    average_steepness = total_steepness / count_steepness if count_steepness > 0 else 0

    # 5. Average Street Length
    total_length = 0
    count_length = 0
    for edge in Edge.objects.filter(city=city):
        total_length += edge.geom.length
        count_length += 1
    average_street_length = total_length / count_length if count_length > 0 else 0

    # 6. Intersection Density
    intersections = Node.objects.filter(city=city, edgenode__edge__city=city).annotate(edge_count=Count('edgenode'))
    intersection_count = intersections.filter(edge_count__gte=3).count()
    intersection_density = intersection_count / city.built_up_area_km2 if city.built_up_area_km2 > 0 else 0

    # 7. Walking/Driving Segments Ratio
    walking_edges = Edge.objects.filter(city=city, is_pedestrian=True).count()
    driving_edges = Edge.objects.filter(city=city, is_driving=True).count()
    walking_driving_ratio = walking_edges / driving_edges if driving_edges > 0 else 0

    # 8. Biking/Driving Segments Ratio
    biking_edges = Edge.objects.filter(city=city, is_cycling=True).count()
    biking_driving_ratio = biking_edges / driving_edges if driving_edges > 0 else 0

    # 9. Average Biking Score
    total_biking_score = 0
    count_biking = 0
    for edge in Edge.objects.filter(city=city):
        biking_score = calculate_biking_score(edge.speed_limit, edge.is_cycling)
        total_biking_score += biking_score
        count_biking += 1

    average_biking_score = total_biking_score / count_biking if count_biking > 0 else 0

    # 10. Average Walking Score
    total_walking_score = 0
    count_walking = 0
    for edge in Edge.objects.filter(city=city):
        walking_score = calculate_walking_score(edge.speed_limit, edge.is_pedestrian)
        total_walking_score += walking_score
        count_walking += 1

    average_walking_score = total_walking_score / count_walking if count_walking > 0 else 0

    # 11. Connectivity
    nodes = Node.objects.filter(city=city)
    total_degree = 0
    node_count = nodes.count()

    for node in nodes:
        degree = EdgeNode.objects.filter(node=node).count()
        total_degree += degree

    connectivity = total_degree / node_count if node_count > 0 else 0

    # 返回所有指标
    return {
        'average_circuity': average_circuity,
        'street_angle_entropy': entropy,
        'road_density': road_density,
        'average_steepness': average_steepness,
        'average_street_length': average_street_length,
        'intersection_density': intersection_density,
        'walking_driving_ratio': walking_driving_ratio,
        'biking_driving_ratio': biking_driving_ratio,
        'average_biking_score': average_biking_score,
        'average_walking_score': average_walking_score,
        'connectivity': connectivity
    }


def calculate_distance(node1, node2):
    from math import radians, cos, sin, asin, sqrt

    lon1, lat1 = node1.geom.x, node1.geom.y
    lon2, lat2 = node2.geom.x, node2.geom.y
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371000
    return c * r


def calculate_bearing(geom):
    from math import atan2, degrees, radians, sin, cos

    start_point = geom.coords[0]
    end_point = geom.coords[-1]

    lon1, lat1 = start_point
    lon2, lat2 = end_point

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1

    x = sin(dlon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)

    initial_bearing = atan2(x, y)
    initial_bearing = degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


def calculate_biking_score(speed_limit, has_cycling_lane):
    if speed_limit is not None:
        if has_cycling_lane:
            if speed_limit <= 30:
                return 1.0
            elif speed_limit <= 50:
                return 0.8
            else:
                return 0.6
        else:
            if speed_limit <= 30:
                return 0.6
            else:
                return 0.3
    else:
        return 0.7 if has_cycling_lane else 0.3


def calculate_walking_score(speed_limit, has_pedestrian_access):
    if speed_limit is not None:
        if has_pedestrian_access:
            if speed_limit <= 30:
                return 1.0
            elif speed_limit <= 50:
                return 0.8
            else:
                return 0.6
        else:
            if speed_limit <= 30:
                return 0.5
            else:
                return 0.3
    else:
        return 0.7 if has_pedestrian_access else 0.3
