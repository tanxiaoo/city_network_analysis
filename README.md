# City Network Analysis

This is the repository for the projects of the Geoinformatics Project course held in 2025 at Polimi.

**Supervisors**: Juan Pablo Duque, Maria Brovelli

## Project Overview

This project aims to develop an automated pipeline to extract urban street network data from OpenStreetMap (OSM), compute network-based walkability and bikeability indicators, and build a WebGIS system to enable users to compare and match similar cities based on street network features.

The project methodology is inspired by recent research utilizing multimodal and multiscale street network representations.

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
