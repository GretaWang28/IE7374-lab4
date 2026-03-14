import functions_framework
import yaml
import logging
from google.cloud import bigquery

# Configuration
PROJECT_ID = "project-5747f112-c4b8-46c9-b20"       # 🔁 Replace with your GCP project ID
DATASET_ID = "staging"               # Must match the dataset you create in BigQuery

logging.basicConfig(level=logging.INFO)


@functions_framework.cloud_event
def hello_gcs(cloud_event):
    """Entry point: triggered when a file is uploaded to GCS."""
    data = cloud_event.data

    bucket_name = data["bucket"]
    file_name   = data["name"]

    logging.info(f"Event received for file: {file_name} in bucket: {bucket_name}")

    streaming(bucket_name, file_name)


def streaming(bucket_name, file_name):
    """Determines the schema and loads the file into BigQuery."""
    # Derive table name from file name (e.g., "orders.json" → "orders")
    table_name = file_name.split(".")[0]

    # Load schemas from YAML
    with open("schemas.yaml", "r") as f:
        all_schemas = yaml.safe_load(f)

    if table_name not in all_schemas:
        logging.error(f"No schema found for table: {table_name}. Skipping.")
        return

    table_schema = all_schemas[table_name]
    bq_schema    = create_schema_from_yaml(table_schema)

    _check_if_table_exists(table_name, bq_schema)
    _load_table_from_uri(bucket_name, file_name, bq_schema, table_name)


def _check_if_table_exists(table_name, table_schema):
    """Creates the BigQuery table if it doesn't already exist."""
    client   = bigquery.Client()
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    try:
        client.get_table(table_id)
        logging.info(f"Table {table_id} already exists.")
    except Exception:
        logging.info(f"Table {table_id} not found. Creating it...")
        table = bigquery.Table(table_id, schema=table_schema)
        client.create_table(table)
        logging.info(f"Table {table_id} created successfully.")


def _load_table_from_uri(bucket_name, file_name, table_schema, table_name):
    """Loads data from GCS into BigQuery."""
    client   = bigquery.Client()
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    uri      = f"gs://{bucket_name}/{file_name}"

    job_config = bigquery.LoadJobConfig(
        schema=table_schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    load_job = client.load_table_from_uri(uri, table_id, job_config=job_config)
    load_job.result()  # Wait for the job to complete

    logging.info(f"Loaded {load_job.output_rows} rows into {table_id}.")


def create_schema_from_yaml(table_schema):
    """Converts YAML schema definition into BigQuery SchemaField objects."""
    bq_fields = []

    for field in table_schema:
        if field["type"] == "RECORD" and "fields" in field:
            # Handle nested (RECORD) fields recursively
            nested = create_schema_from_yaml(field["fields"])
            bq_fields.append(
                bigquery.SchemaField(field["name"], "RECORD",
                                     mode=field.get("mode", "NULLABLE"),
                                     fields=nested)
            )
        else:
            bq_fields.append(
                bigquery.SchemaField(field["name"], field["type"],
                                     mode=field.get("mode", "NULLABLE"))
            )

    return bq_fields