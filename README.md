# City Network Analysis
This is the repository for the projects of the Geoinformatics Project course held in 2025 at Polimi.
**Supervisors**: Juan Pablo Duque, Maria Brovelli

## Project Overview
This project aims to develop an automated pipeline to extract urban street network data from OpenStreetMap (OSM), compute network-based walkability and bikeability indicators, and build a WebGIS system to enable users to compare and match similar cities based on street network features.

## Data Sources
- **OpenStreetMap (OSM)**: Global open-source street network data.
- **NASADEM**: Global digital elevation model (30m resolution) for obtaining node elevation.
- **GHS Urban Centre Database (GHS-UCDB R2024A)**: Provides city boundaries and built-up areas.

## Project Structure
```text
city_network_analysis/
├── manage.py
├── city_network_analysis/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── streets/
    ├── migrations/
    ├── templates/
    │   ├── city_metrics.html
    │   └── db_map.html
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── utils.py
    ├── data.py
    └── tests.py
```
## Workflow
### Data Extraction
- Download city street networks (driving, walking, cycling) using OSMnx.
- Download NASADEM data
- Download city boundaries and built-up areas data from GHS Urban Centre Database

### Data Preprocessing
- Filter redundant pedestrian paths and cycling lanes.
- Interpolate elevation data from NASADEM.
- Compute edge slope and orientation attributes.

### Metric Calculation
- Calculate approximately 11 network indicators (e.g., average circuity, orientation entropy, road density, average steepness, intersection density).

### Database Storage
- Store cities, street networks, and calculated metrics in a PostgreSQL + PostGIS database.

### WebGIS Development
- Interactive visualization using Leaflet.
- Backend API to query metrics and find similar cities.

## Database
```mermaid
erDiagram
    GeoAreaMapping ||--o{ City : "geo_area"
    City ||--o{ Node : "id"
    City ||--o{ Edge : "id"
    City ||--|| CityWalkabilityMetrics : "id"
    City ||--|| CityBikeabilityMetrics : "id"
    Edge ||--o{ EdgeNode : "id"
    Node ||--o{ EdgeNode : "id"

    GeoAreaMapping {
        string geo_area PK
        string full_name
    }

    City {
        int id PK
        string city_name
        string country
        string geo_area FK
        float area_km2
        float built_up_area_km2
        multipolygon geom
    }

    Node {
        int id PK
        int city FK
        float lat
        float lon
        float elevation
        point geom
    }

    Edge {
        string id PK
        int city FK
        string name
        boolean is_pedestrian
        boolean is_cycling
        boolean is_driving
        integer speed_limit
        string street_type
        linestring geom
    }

    EdgeNode {
        int id PK
        string edge FK
        int node FK
        integer position
    }

    CityWalkabilityMetrics {
        int id PK
        int city FK
        integer POP
        float CIR
        float ORE
        float RDE
        float AST
        float ASL
        float IND
        float WDR
        float AWS
        float ACO
        float SCO
    }

    CityBikeabilityMetrics {
        int id PK
        int city FK
        integer POP
        float CIR
        float ORE
        float RDE
        float AST
        float ASL
        float IND
        float BDR
        float ABS
        float ACO
        float SCO
    }
```

## Dashboard
The project includes an interactive dashboard to visualize and explore the urban street network metrics for different cities. It provides three main views that you can access via the following URLs:

### 1. Map View
URL: [http://localhost:8000/db_map/](http://localhost:8000/db_map/)
This page displays an interactive map of the city's street network, allowing users to explore the spatial distribution of streets, nodes, and other features.

![Map View](streets/static/img/map.jpg)

### 2. City Metrics
URL: [http://localhost:8000/city-metrics/](http://localhost:8000/city-metrics/)
This page provides various metrics for each city, such as walkability, bikeability, and connectivity scores. The metrics are calculated based on the network structure and are displayed in a user-friendly format.
![City Metrics](streets/static/img/city_metrics.jpg)

### 3. Similar Cities
URL: [http://localhost:8000/similar-cities/](http://localhost:8000/similar-cities/)
This page allows users to compare cities based on their street network metrics. The dashboard will display a list of cities that are similar to the selected city, based on the final similarity score.
![Similar Cities](streets/static/img/similar_cities.jpg)
