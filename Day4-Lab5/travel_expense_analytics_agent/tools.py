"""Tools for Travel Expense Analytics Agent."""

import os
import json
import mimetypes
from typing import Literal, Optional, List, Dict, Any
from google.cloud import storage, secretmanager
from google import genai
from google.genai import types
from google.cloud.alloydb.connector import Connector, IPTypes
from pydantic import BaseModel, Field


class ExpenseDoc(BaseModel):
    """Schema for extracted expense document details."""
    category: Literal['taxi invoice', 'hotel bill', 'flight booking'] = Field(
        description="Category of the travel expense document. Must be exactly one of: 'taxi invoice', 'hotel bill', or 'flight booking'."
    )
    transaction_date: str = Field(
        description="Transaction date in YYYY-MM-DD format."
    )
    amount_usd: float = Field(
        description="Transaction amount in USD as a floating point number."
    )


def gcs_expense_processor(
    bucket_name: str = "qwiklabs-gcp-00-2b6a20ee6e06-cepf",
    prefix: str = "cymbal_group_expenses/",
    gcs_uri: Optional[str] = None,
    output_json_name: str = "travel_receipts.json",
) -> Dict[str, Any]:
    """Connects to Google Cloud Storage, processes unstructured expense documents (receipts, invoices, images),
    classifies each document into a travel category, extracts transaction date and amount in USD,
    saves the processed output as travel_receipts.json in the Cloud Storage bucket,
    and returns a summary table along with structured document data.

    Args:
        bucket_name: Name of the Cloud Storage bucket.
        prefix: Prefix/folder path in the bucket containing expense files.
        gcs_uri: Optional full GCS URI (e.g. 'gs://qwiklabs-gcp-00-2b6a20ee6e06-cepf/cymbal_group_expenses/').
        output_json_name: Target blob name for saving processed JSON output in GCS.

    Returns:
        Dict containing processed count, total amount, detailed expense records, output file GCS URI, and formatted markdown summary table.
    """
    if gcs_uri and gcs_uri.startswith("gs://"):
        uri_parts = gcs_uri[5:].split("/", 1)
        bucket_name = uri_parts[0]
        prefix = uri_parts[1] if len(uri_parts) > 1 else ""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))

    # Filter out directory placeholders and existing output JSON files
    expense_blobs = [
        b for b in blobs 
        if not b.name.endswith("/") and not b.name.endswith(".json")
    ]

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-2b6a20ee6e06")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

    genai_client = genai.Client(
        vertexai=True,
        location=location,
        project=project,
    )

    results: List[Dict[str, Any]] = []
    total_amount = 0.0

    for blob in expense_blobs:
        file_bytes = blob.download_as_bytes()
        file_name = blob.name.split("/")[-1]
        blob_gcs_uri = f"gs://{bucket_name}/{blob.name}"

        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            mime_type = blob.content_type or "application/octet-stream"

        response = genai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                (
                    "Inspect and extract details from this expense document following the schema. "
                    "Classify into exactly one category: 'taxi invoice', 'hotel bill', or 'flight booking'. "
                    "Extract the transaction date as YYYY-MM-DD and amount in USD."
                ),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExpenseDoc,
            ),
        )

        extracted = ExpenseDoc.model_validate_json(response.text)
        record = {
            "file_name": file_name,
            "gcs_uri": blob_gcs_uri,
            "category": extracted.category,
            "transaction_date": extracted.transaction_date,
            "amount_usd": extracted.amount_usd,
        }
        results.append(record)
        total_amount += extracted.amount_usd

    total_amount = round(total_amount, 2)

    # Save processed output as JSON in Cloud Storage
    output_data = {
        "bucket": bucket_name,
        "processed_count": len(results),
        "total_amount_usd": total_amount,
        "expenses": results,
    }
    
    # Save to root of bucket
    output_blob = bucket.blob(output_json_name)
    output_blob.upload_from_string(
        json.dumps(output_data, indent=2),
        content_type="application/json"
    )
    saved_gcs_uri = f"gs://{bucket_name}/{output_json_name}"

    # Also save if prefix is specified
    if prefix and prefix.rstrip("/") != "":
        prefix_json_key = f"{prefix.rstrip('/')}/{output_json_name}"
        prefix_blob = bucket.blob(prefix_json_key)
        prefix_blob.upload_from_string(
            json.dumps(output_data, indent=2),
            content_type="application/json"
        )

    # Build Markdown summary table
    table_lines = [
        "| File Name | Category | Transaction Date | Amount (USD) | GCS URI |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in results:
        table_lines.append(
            f"| {r['file_name']} | {r['category']} | {r['transaction_date']} | ${r['amount_usd']:.2f} | {r['gcs_uri']} |"
        )
    table_lines.append(f"| **Total** | | | **${total_amount:.2f}** | |")

    summary_table = "\n".join(table_lines)

    return {
        "status": "success",
        "processed_count": len(results),
        "total_amount_usd": total_amount,
        "output_gcs_uri": saved_gcs_uri,
        "expenses": results,
        "summary_table": summary_table,
    }


def alloydb_expense_analytics(
    year: int = 2025,
    secret_name: str = "alloydb-password",
    bucket_name: str = "qwiklabs-gcp-00-2b6a20ee6e06-cepf",
    output_json_name: str = "travel_expenses.json",
) -> Dict[str, Any]:
    """Connects to AlloyDB PostgreSQL using google-cloud-alloydb-connector with IAM auth,
    retrieves the database credentials, executes an aggregation query for overall travel
    expenses for the specified year grouped by team and month, saves the results as travel_expenses.json in Cloud Storage,
    and formats the output as a Markdown table.

    Args:
        year: Target year to aggregate expenses for (default 2025).
        secret_name: Name of the Secret Manager secret containing the database password.
        bucket_name: Cloud Storage bucket name to save output JSON into.
        output_json_name: Name of the JSON output file to store in GCS (default 'travel_expenses.json').

    Returns:
        Dict containing status, row count, total amount, GCS output URI, records list, and formatted Markdown table.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-2b6a20ee6e06")
    instance_uri = os.environ.get(
        "ALLOYDB_INSTANCE",
        f"projects/{project_id}/locations/us-central1/clusters/cepf-elevate-expenses/instances/cepf-elevate-expenses-primary"
    )
    user = os.environ.get("ALLOYDB_USER", "student-01-cf96e7be9feb@qwiklabs.net")
    db_name = os.environ.get("ALLOYDB_DATABASE", "postgres")

    # Fetch password from Secret Manager
    try:
        sm_client = secretmanager.SecretManagerServiceClient()
        sec_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        sec_res = sm_client.access_secret_version(request={"name": sec_path})
        password = sec_res.payload.data.decode("UTF-8").strip()
    except Exception:
        password = os.environ.get("ALLOYDB_PASSWORD", "Password01")

    connector = Connector()

    try:
        conn = connector.connect(
            instance_uri,
            "pg8000",
            user=user,
            password=password,
            db=db_name,
            ip_type=IPTypes.PUBLIC,
            enable_iam_auth=True,
        )
        cursor = conn.cursor()

        query = f"""
        SELECT 
            team AS team_name,
            EXTRACT(MONTH FROM expense_date)::integer AS month,
            SUM(amount) AS total_amount_usd
        FROM travel_expenses
        WHERE EXTRACT(YEAR FROM expense_date) = {int(year)}
        GROUP BY team, EXTRACT(MONTH FROM expense_date)
        ORDER BY team_name, month;
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        records = []
        overall_total = 0.0

        for row in rows:
            team_name = row[0]
            month_val = int(row[1])
            total_amt = float(row[2])
            overall_total += total_amt
            records.append({
                "team_name": team_name,
                "month": month_val,
                "total_amount_usd": round(total_amt, 2),
            })

        overall_total = round(overall_total, 2)

        # Save aggregated results to Cloud Storage
        output_data = {
            "bucket": bucket_name,
            "year": year,
            "row_count": len(records),
            "overall_total_usd": overall_total,
            "records": records,
        }

        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            
            # Save at root of bucket
            output_blob = bucket.blob(output_json_name)
            output_blob.upload_from_string(
                json.dumps(output_data, indent=2),
                content_type="application/json"
            )
            saved_gcs_uri = f"gs://{bucket_name}/{output_json_name}"

            # Also save inside cymbal_group_expenses/ prefix if present
            prefix_blob = bucket.blob(f"cymbal_group_expenses/{output_json_name}")
            prefix_blob.upload_from_string(
                json.dumps(output_data, indent=2),
                content_type="application/json"
            )
        except Exception as st_err:
            saved_gcs_uri = f"gs://{bucket_name}/{output_json_name} (error saving: {st_err})"

        # Build Markdown summary table
        table_lines = [
            "| Team Name | Month | Total Amount (USD) |",
            "| --- | --- | --- |",
        ]
        for rec in records:
            table_lines.append(
                f"| {rec['team_name']} | {rec['month']} | ${rec['total_amount_usd']:.2f} |"
            )
        table_lines.append(f"| **Overall Total** | | **${overall_total:.2f}** |")

        summary_table = "\n".join(table_lines)

        return {
            "status": "success",
            "year": year,
            "row_count": len(records),
            "overall_total_usd": overall_total,
            "output_gcs_uri": saved_gcs_uri,
            "records": records,
            "summary_table": summary_table,
        }

    finally:
        try:
            conn.close()
        except Exception:
            pass
        connector.close()
