import ast
import json
import osmnx as ox
from django.contrib.gis.geos import Point
from django.contrib.gis.geos import LineString
from .models import City, Node, Edge, MetricValue, Metric
from math import log
from django.utils import timezone
import numpy as np
import networkx as nx
from django.core.exceptions import ObjectDoesNotExist


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


def save_nodes(city_name: str, nodes_gdf):
    nodes_geojson = json.loads(nodes_gdf.to_json())
    city = City.objects.get(name=city_name)

    for feature in nodes_geojson["features"]:
        osm_id = int(feature["id"])
        coords = feature["geometry"]["coordinates"]
        point = Point(coords)

        Node.objects.update_or_create(
            osm_id=osm_id,
            city=city,
            defaults={
                'elevation': None,
                'geom': point
            }
        )

    print(f"Saved {len(nodes_geojson['features'])} nodes to the database.")


def save_edges(city_name: str, edges_gdf, modality: str = "drive"):
    highway_type_mapping = {
        'motorway': 'highway',
        'motorway_link': 'highway',
        'trunk': 'highway',
        'trunk_link': 'highway',
        'primary': 'urban',
        'primary_link': 'urban',
        'secondary': 'urban',
        'secondary_link': 'urban',
        'tertiary': 'urban',
        'unclassified': 'rural',
        'residential': 'rural',
        'living_street': 'rural',
        'service': 'alley',
        'track': 'alley',
        'path': 'alley',
    }

    edges_geojson = json.loads(edges_gdf.to_json())
    city = City.objects.get(name=city_name)

    for feature in edges_geojson['features']:
        properties = feature['properties']
        coords = feature['geometry']['coordinates']

        edge_id = feature['id']
        u, v, _ = map(int, edge_id.strip('()').split(', '))
        try:
            start_node = Node.objects.get(osm_id=u, city=city)
            end_node = Node.objects.get(osm_id=v, city=city)
        except Node.DoesNotExist:
            print(f"Edge skipped: Node {u} or {v} not found.")
            continue

        name = properties.get('name')

        maxspeed = properties.get('maxspeed')
        speed_limit = (
            int(maxspeed[0]) if isinstance(maxspeed, list) and maxspeed else
            int(maxspeed) if isinstance(maxspeed, str) and maxspeed.isdigit() else None
        )

        highway_type = properties.get('highway', '')
        if isinstance(highway_type, list):
            highway_type = set(highway_type)
        else:
            highway_type = {highway_type}

        edge_type = None
        for ht in highway_type:
            mapped_type = highway_type_mapping.get(ht, 'unknown')
            if mapped_type != 'unknown':
                edge_type = mapped_type
                break

        if edge_type is None:
            continue

        valid_modes = {
            "drive": "driving",
            "walk": "pedestrian",
            "bike": "cycling",
            "public_transport": "public_transport"
        }
        mode = valid_modes.get(modality, None)

        geom = LineString([tuple(coord) for coord in coords])

        # Remove 'id' from update_or_create
        Edge.objects.update_or_create(
            city=city,
            start_node=start_node,
            end_node=end_node,
            defaults={
                'geom': geom,
                'data': {
                    'name': name,
                    'length': feature['properties'].get('length'),
                    'mode': mode,
                    'speed_limit': speed_limit,
                    'edge_type': edge_type
                }
            }
        )

    print(f"Saved {len(edges_geojson['features'])} edges to the database.")


def save_graphml_nodes(city_name: str, graphml_path: str, ):
    try:
        city = City.objects.get(name=city_name)
    except City.DoesNotExist:
        print(f"City {city_name} not found.")
        return

    print(f"Importing {city.name} graphml file...")
    G = nx.read_graphml(graphml_path)

    created_count = 0
    skipped_count = 0
    sample_node = list(G.nodes(data=True))[0]
    print(f"Sample node data: {sample_node}")

    for node_id, data in G.nodes(data=True):
        osm_id = data.get('osmid', node_id)
        try:
            x = float(data['x'])
            y = float(data['y'])
        except(TypeError, ValueError):
            skipped_count += 1
            continue

        obj, created = Node.objects.update_or_create(
            osm_id=osm_id,
            city=city,
            defaults={
                'elevation': float(data.get('elevation', 0.0)),
                'geom': Point(x, y),
            }

        )

        if created:
            created_count += 1

    print(f"Nodes imported or updated: {created_count}, skipped: {skipped_count}")


def save_graphml_edges(city_name: str, graphml_path: str):
    try:
        city = City.objects.get(name=city_name)
    except City.DoesNotExist:
        print(f"City {city_name} not found.")
        return

    print(f"Importing edges for {city.name} from graphml file...")
    G = nx.read_graphml(graphml_path)

    created_count = 0
    skipped_count = 0

    for source, target, edge_data in G.edges(data=True):
        try:
            start_node = Node.objects.get(osm_id=int(source), city=city)
            end_node = Node.objects.get(osm_id=int(target), city=city)
        except (ObjectDoesNotExist, ValueError, KeyError) as e:
            print(f"Skipping edge  {source}→{target}: node lookup failed - {e}")
            skipped_count += 1
            continue

        try:
            wkt_geom = edge_data['geometry']
            coords_str = wkt_geom.replace('LINESTRING (', '').replace(')', '')
            coords = [tuple(map(float, point.split())) for point in coords_str.split(', ')]
            linestring = LineString(coords)
        except (KeyError, ValueError, AttributeError) as e:
            print(f"Skipping edge {source}→{target}: invalid geometry - {e}")
            skipped_count += 1
            continue

        edge, created = Edge.objects.update_or_create(
            city=city,
            start_node=start_node,
            end_node=end_node,
            defaults={
                'geom': linestring,
            }
        )

        if created:
            created_count += 1

    print(f"Edges imported: {created_count}, skipped: {skipped_count}")


# def save_graphml_edges(city_name: str, graphml_path: str):
#     try:
#         city = City.objects.get(name=city_name)
#     except City.DoesNotExist:
#         print(f"City {city_name} not found.")
#         return
#
#     print(f"Importing edges for {city.name} from graphml file...")
#     G = nx.read_graphml(graphml_path)
#
#     created_count = 0
#     skipped_count = 0
#
#     for source, target, edge_data in G.edges(data=True):
#         try:
#             start_node = Node.objects.get(osm_id=int(source), city=city)
#             end_node = Node.objects.get(osm_id=int(target), city=city)
#         except (ObjectDoesNotExist, ValueError, KeyError) as e:
#             print(f"Skipping edge  {source}→{target}: node lookup failed - {e}")
#             skipped_count += 1
#             continue
#
#         try:
#             wkt_geom = edge_data['geometry']
#             coords_str = wkt_geom.replace('LINESTRING (', '').replace(')', '')
#             coords = [tuple(map(float, point.split())) for point in coords_str.split(', ')]
#             linestring = LineString(coords)
#         except (KeyError, ValueError, AttributeError) as e:
#             print(f"Skipping edge {source}→{target}: invalid geometry - {e}")
#             skipped_count += 1
#             continue
#
#         valid_edge_types = ['highway', 'urban', 'rural', 'alley']
#
#         edge_attributes = {
#             'name': edge_data.get('name'),
#             'length': parse_float(edge_data.get('length', 0)),
#             'mode': edge_data.get('driving'),  # valid_modes = ['pedestrian', 'driving', 'cycling', 'public_transport']
#             'speed_limit': parse_float(edge_data.get('maxspeed', 0)),
#             'edge_type': edge_data.get('highway') if edge_data.get('highway') in valid_edge_types else None
#         }
#
#         edge, created = Edge.objects.update_or_create(
#             city=city,
#             start_node=start_node,
#             end_node=end_node,
#             defaults={
#                 'geom': linestring,
#                 'data': edge_attributes
#             }
#         )
#
#         if created:
#             created_count += 1
#
#     print(f"Edges imported: {created_count}, skipped: {skipped_count}")


def parse_float(value):
    try:
        return float(value)
    except ValueError:
        try:
            value_list = ast.literal_eval(value)
            if isinstance(value_list, list) and value_list:
                return float(value_list[0])
        except (ValueError, SyntaxError):
            pass
    return 0.0


def save_metric_values(city_name: str):
    try:
        city = City.objects.get(name=city_name)
    except City.DoesNotExist:
        print(f"City {city_name} not found.")
        return

    now = timezone.now()

    metrics_result = calculate_urban_metrics(city_name)

    for metric_key, value in metrics_result.items():
        try:
            metric_name, metric_type = metric_key.split('_')
        except ValueError:
            print(f"Invalid metric key format: {metric_key}. Skipping.")
            continue

        try:
            metric = Metric.objects.get(name=metric_name, type=metric_type)
        except Metric.DoesNotExist:
            print(f"Metric {metric_name} with type {metric_type} not found. Skipping.")
            continue

        MetricValue.objects.update_or_create(
            city=city,
            metric=metric,
            datetime=now,
            defaults={'value': value}
        )

    print(f"Metric values for {city_name} have been successfully saved.")


def calculate_urban_metrics(city_name: str):
    city = City.objects.get(name=city_name)

    # 1. Average Circuity
    total_circuity = 0
    count_circuity = 0
    for edge in Edge.objects.filter(city=city).select_related('start_node', 'end_node'):
        node1, node2 = edge.start_node, edge.end_node
        if node1 and node2:
            straight_distance = calculate_distance(node1, node2)
            if straight_distance > 0:
                circuity = edge.geom.length / straight_distance  # 使用 geom 的 length 属性
                total_circuity += circuity
                count_circuity += 1
    average_circuity = total_circuity / count_circuity if count_circuity > 0 else 0

    # 2. Orientation Entropy
    street_angles = []
    for edge in Edge.objects.filter(city=city):
        angle = calculate_bearing(edge.geom)
        street_angles.append(angle)
    angle_counts = [0] * 36
    for angle in street_angles:
        angle_index = int(angle // 10)
        angle_counts[angle_index] += 1
    total_angles = len(street_angles)
    entropy = -sum((count / total_angles) * log(count / total_angles) for count in angle_counts if count > 0)

    # 3. Road Density
    total_street_segments = Edge.objects.filter(city=city).count()
    road_density = total_street_segments / city.built_up_area_km2 if city.built_up_area_km2 > 0 else 0

    # 4. Average Steepness
    total_steepness = 0
    count_steepness = 0
    for edge in Edge.objects.filter(city=city).select_related('start_node', 'end_node'):
        node1, node2 = edge.start_node, edge.end_node
        if node1 and node2:
            elevation_difference = abs(
                node1.elevation - node2.elevation) if node1.elevation is not None and node2.elevation is not None else 0
            horizontal_distance = edge.geom.length  # 直接使用 geom 的长度作为水平距离
            if horizontal_distance > 0:
                steepness = elevation_difference / horizontal_distance
                total_steepness += steepness
                count_steepness += 1
    average_steepness = total_steepness / count_steepness if count_steepness > 0 else 0

    # 5. Average Street Length
    edge_lengths = Edge.objects.filter(city=city).values_list('geom', flat=True)
    total_length = sum(edge.geom.length for edge in Edge.objects.filter(city=city))  # 使用 geom.length
    count_length = Edge.objects.filter(city=city).count()
    average_street_length = total_length / count_length if count_length > 0 else 0

    # 6. Intersection Density
    all_nodes = Node.objects.filter(city=city)
    node_edge_counts = {node.id: 0 for node in all_nodes}
    for edge in Edge.objects.filter(city=city).select_related('start_node', 'end_node'):
        if edge.start_node_id in node_edge_counts:
            node_edge_counts[edge.start_node_id] += 1
        if edge.end_node_id in node_edge_counts:
            node_edge_counts[edge.end_node_id] += 1
    intersection_count = sum(1 for count in node_edge_counts.values() if count >= 3)
    intersection_density = intersection_count / city.built_up_area_km2 if city.built_up_area_km2 > 0 else 0

    # 7. Walking/Driving Segments Ratio
    walking_edges = Edge.objects.filter(city=city, data__mode='pedestrian').count()
    driving_edges = Edge.objects.filter(city=city, data__mode='driving').count()
    walking_driving_ratio = walking_edges / driving_edges if driving_edges > 0 else 0

    # 8. Biking/Driving Segments Ratio
    biking_edges = Edge.objects.filter(city=city, data__mode='cycling').count()
    biking_driving_ratio = biking_edges / driving_edges if driving_edges > 0 else 0

    # 9. Average Biking Score
    total_biking_score = 0
    count_biking = 0
    for edge in Edge.objects.filter(city=city):
        biking_score = calculate_biking_score(edge.data.get('speed_limit', 0), edge.data.get('mode') == 'cycling')
        total_biking_score += biking_score
        count_biking += 1
    average_biking_score = total_biking_score / count_biking if count_biking > 0 else 0

    # 10. Average Walking Score
    total_walking_score = 0
    count_walking = 0
    for edge in Edge.objects.filter(city=city):
        walking_score = calculate_walking_score(edge.data.get('speed_limit', 0), edge.data.get('mode') == 'pedestrian')
        total_walking_score += walking_score
        count_walking += 1
    average_walking_score = total_walking_score / count_walking if count_walking > 0 else 0

    # 11. Connectivity
    node_edge_counts = {node.id: 0 for node in all_nodes}  # Reinitialize node_edge_counts
    for edge in Edge.objects.filter(city=city).select_related('start_node', 'end_node'):
        node_edge_counts[edge.start_node_id] += 1
        node_edge_counts[edge.end_node_id] += 1
    total_degree = sum(node_edge_counts.values())
    node_count = len(node_edge_counts)
    connectivity = total_degree / node_count if node_count > 0 else 0
    degrees = list(node_edge_counts.values())
    connectivity_std = np.std(degrees) if degrees else 0

    return {
        'CIR_walk': average_circuity,
        'CIR_bike': average_circuity,
        'ORE_walk': entropy,
        'ORE_bike': entropy,
        'RDE_walk': road_density,
        'RDE_bike': road_density,
        'AST_walk': average_steepness,
        'AST_bike': average_steepness,
        'ASL_walk': average_street_length,
        'ASL_bike': average_street_length,
        'IND_walk': intersection_density,
        'IND_bike': intersection_density,
        'WDR_walk': walking_driving_ratio,
        'BDR_bike': biking_driving_ratio,
        'AWS_walk': average_walking_score,
        'ABS_bike': average_biking_score,
        'ACO_walk': connectivity,
        'ACO_bike': connectivity,
        'SCO_walk': connectivity_std,
        'SCO_bike': connectivity_std,
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


