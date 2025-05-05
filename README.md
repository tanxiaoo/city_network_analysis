# City Network Analysis
This is the repository for the projects of the Geoinformatics Project course held in 2025 at Polimi.
**Supervisors**: Juan Pablo Duque, Maria Brovelli

## Project Overview
This project analyzes urban mobility using street network data from OpenStreetMap (OSM). The goal is to develop a backend system for storing and managing street networks and mobility metrics, allowing for comparative analysis of cities based on street characteristics.

The backend includes a database and API service to store, process, and manage street network data, compute mobility indicators, and provide data access.
## Project Structure
```text
city_network_analysis/
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
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── README.md
├── Report.md
├── requirements.txt
└── Urban Metrics API.postman_collection.json

```

## Database
```mermaid
erDiagram
    GeoAreaMapping ||--o{ City : "has"
    City ||--o{ Node : "has"
    City ||--o{ Edge : "has"
    City ||--o{ MetricValue : "has"
    Metric ||--o{ MetricValue : "has"
    Node ||--o{ Edge : "start_node"
    Node ||--o{ Edge : "end_node"

    GeoAreaMapping {
        char geo_area PK "Primary key (2-char code)"
        string full_name "Full name of geographic area"
    }

    City {
        int id PK "Primary key"
        string name "City name (unique)"
        string country "Country name"
        char geo_area FK "FK to GeoAreaMapping"
        int population "Population (optional)"
        float area_km2 "Total area in square km"
        float built_up_area_km2 "Built-up area in square km"
        multipolygon geom "Geometry of city (optional)"
    }

    Metric {
        int id PK "Primary key"
        string name "Metric name"
        string type "walk or bike"
    }

    MetricValue {
        int id PK "Primary key"
        int metric_id FK "FK to Metric"
        int city_id FK "FK to City"
        float value "Metric value"
        datetime datetime "Timestamp of record"
    }

    Node {
        int id PK "Primary key"
        int city_id FK "FK to City"
        bigint osm_id "OpenStreetMap node ID (optional, unique)"
        float elevation "Elevation (optional)"
        point geom "Geographic point"
    }

    Edge {
        int id PK "Primary key"
        int city_id FK "FK to City"
        int start_node_id FK "FK to Node (start)"
        int end_node_id FK "FK to Node (end)"
        linestring geom "Geographic line"
        json data "Includes: name, length (m), mode, speed_limit (km/h), edge_type"
    }
```
## API Design

This API provides endpoints for managing urban metrics data including cities, measurement metrics, network nodes, and edges.

**Base URL**: `http://localhost:8000/api/`

All responses are in JSON format.

## Postman Collection

A full Postman collection is provided for testing and reproducibility.

### Available Endpoints

#### City Endpoints
- `GET /api/cities/` - Get All Cities
- `POST /api/cities/` - Create City
- `PUT /api/cities/{id}/` - Update City
- `DELETE /api/cities/{id}/` - Delete City

#### Metric Endpoints
- `GET /api/metrics/` - Get All Metrics
- `POST /api/metrics/` - Create Metric
- `PUT /api/metrics/{id}/` - Update Metric
- `DELETE /api/metrics/{id}/` - Delete Metric

#### MetricValue Endpoints
- `GET /api/metricvalues/` - Get All Metric Values
- `GET /api/metricvalues/filtered/` - Get Filtered Metric Values
- `POST /api/metricvalues/` - Create MetricValue
- `PUT /api/metricvalues/{id}/` - Update MetricValue
- `DELETE /api/metricvalues/{id}/` - Delete MetricValue

#### Node Endpoints
- `GET /api/nodes/` - Get All Nodes
- `GET /api/nodes/city/{city_id}/` - Get Nodes by City
- `POST /api/nodes/` - Create Node
- `PUT /api/nodes/{id}/` - Update Node
- `DELETE /api/nodes/{id}/` - Delete Node

#### Edge Endpoints
- `GET /api/edges/` - Get All Edges
- `GET /api/edges/city/{city_id}/` - Get Edges by City
- `POST /api/edges/` - Create Edge
- `PUT /api/edges/{id}/` - Update Edge
- `DELETE /api/edges/{id}/` - Delete Edge

**Access the collection**:  
- [Postman Collection Link](https://xiaotan-6436217.postman.co/workspace/xiao-tan's-Workspace~73cb4ce1-4af2-4705-896a-9af5177494b9/collection/44577322-cd2a15fa-72f4-4adb-96b3-b6583872cb4c?action=share&creator=44577322)
- You can also import the Urban Metrics API.postman_collection.json file provided in the repository directly into Postman.

## Setup and Installation

### Prerequisites

To run this project, you need to have Docker and Docker Compose installed on your machine.

- [Install Docker](https://www.docker.com/get-started)
- [Install Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clone the Repository

Clone this project to your local machine:
```bash
git clone https://github.com/tanxiaoo/city_network_analysis.git
cd city_network_analysis
```


### 2. Build and Start the Services

Run the following command to build the Docker images and start the services:
```bash
docker-compose up --build
```

This command will:
- Build the Docker images (including Python, Django, and dependencies)
- Start the web service (Django) and database (PostgreSQL)
- Make the project accessible at http://localhost:8000

### 3. Initialize the Database (First Time Only)

If it's your first time running the project, initialize the database with:
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

Where:
- `migrate`: Applies database migrations
- `createsuperuser`: Creates an admin user to access the Django admin interface

### 4. Running the Project

After the initial setup, you can start the project anytime with:
```bash
docker-compose up
```

The web application will be available at http://localhost:8000.