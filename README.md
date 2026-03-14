# IE7374 Lab 4 - ETL Pipeline: Google Cloud Storage to BigQuery

## Overview
This lab implements an automated ETL (Extract, Transform, Load) pipeline that transfers data from a Google Cloud Storage (GCS) bucket to BigQuery using Cloud Run Functions. The pipeline is automatically triggered when a new JSON file is uploaded to the GCS bucket.

## Architecture
```
orders.json → GCS Bucket (lab4_buckets) → Cloud Run Function (etl-function) → BigQuery (staging.orders)
```

## Project Structure
```
lab4/
├── main.py          # Core ETL logic - Cloud Function entry point
├── schemas.yaml     # BigQuery table schema definitions
├── requirements.txt # Python dependencies
└── orders.json      # Sample test data
```

## Files Description

### `main.py`
Contains the main ETL logic with the following functions:
- **`hello_gcs(cloud_event)`** - Entry point triggered by GCS file upload events
- **`streaming(bucket_name, file_name)`** - Orchestrates the ETL process and determines schema
- **`_check_if_table_exists()`** - Creates BigQuery table if it doesn't exist
- **`_load_table_from_uri()`** - Loads data from GCS into BigQuery using NEWLINE_DELIMITED_JSON format
- **`create_schema_from_yaml()`** - Converts YAML schema definitions into BigQuery SchemaField objects

### `schemas.yaml`
Defines the BigQuery table schema for the `orders` table with the following fields:
- `order_id` (STRING)
- `customer_name` (STRING)
- `product` (STRING)
- `quantity` (INTEGER)
- `price` (FLOAT)

### `requirements.txt`
Python dependencies:
- `google-cloud-bigquery`
- `google-cloud-storage`
- `pyyaml`
- `functions-framework`

## GCP Setup

### Prerequisites
- Google Cloud Platform account with billing enabled
- The following APIs enabled:
  - Cloud Functions API
  - Cloud Build API
  - Eventarc API
  - BigQuery API

### Infrastructure
| Resource | Name |
|---|---|
| GCS Bucket | `lab4_buckets` |
| Cloud Run Function | `etl-function` |
| BigQuery Dataset | `staging` |
| BigQuery Table | `orders` |
| Region | `us-central1` |

### IAM Roles (Compute Service Account)
- BigQuery Admin
- Cloud Run Invoker
- Cloud Run Builder
- Eventarc Event Receiver

## How It Works
1. A JSON file (e.g. `orders.json`) is uploaded to the `lab4_buckets` GCS bucket
2. The upload event triggers the `etl-function` Cloud Run Function via Eventarc
3. The function reads the filename and matches it to a schema in `schemas.yaml`
4. If the BigQuery table doesn't exist, it creates it automatically
5. The data is loaded from GCS into the BigQuery `staging` dataset

## Testing
Upload the sample `orders.json` file to the GCS bucket:
```json
{"order_id": "001", "customer_name": "Alice Smith", "product": "Laptop", "quantity": 2, "price": 999.99}
{"order_id": "002", "customer_name": "Bob Jones", "product": "Mouse", "quantity": 5, "price": 19.99}
{"order_id": "003", "customer_name": "Carol White", "product": "Keyboard", "quantity": 3, "price": 49.99}
```

Verify the data in BigQuery:
```sql
SELECT * FROM `project-5747f112-c4b8-46c9-b20.staging.orders`
```

## Results
After uploading `orders.json`, the pipeline successfully:
- Created the `staging.orders` table in BigQuery
- Loaded 3 rows of order data into the table
