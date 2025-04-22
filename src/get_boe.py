import os
import json
import logging
from datetime import datetime
import requests
import pandas as pd
import boto3
from io import StringIO
from process_boe import flatten_boe_data

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_boe_data(date=None, data=None, **kwards):
    """
    Get data from the BOE API for a specific date.

    Args:
        date (datetime, optional): The date to get data for. string format {"Y%%m%d"}. Defaults to today.
        data (json, optional): The data to process. If provided, the function will not make an API request.
            Defaults to None. If data is provided, date is required.

    Returns:
        pandas.DataFrame: A DataFrame containing the flattened BOE data
    """
    mode = "local"
    if kwards:
        if "s3_bucket" in kwards:
            s3_bucket = kwards["s3_bucket"]
            mode = "lambda"
            logger.info("Running in Lambda mode with S3 bucket: %s", s3_bucket)

    if data and date:
        date_str = date

    elif data is None:
        if date is None:
            date_str = datetime.today().strftime('%Y%m%d')
        else:
            date_str = date

        url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{date_str}"
        headers = {"Accept": "application/json"}

        try:
            logger.info("Fetching data from URL: %s", url)
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logger.error("Received status code %d", response.status_code)

            data = response.json()

        except requests.exceptions.RequestException as e:
            logger.error("Error fetching data from BOE API: %s", e)
            return pd.DataFrame()

        else:
            json_output_dir = "output_json"
            output_file = f"boe_data_{date_str}.json"
            output_path = os.path.join("output_json", output_file)

            if mode == "local":
                os.makedirs(json_output_dir, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                logger.info("JSON data saved to %s", output_path)

            elif mode == "lambda":
                save_to_s3(
                    body=json.dumps(data),
                    bucket=s3_bucket,
                    key=output_path,
                    content_type='application/json'
                )
                logger.info("JSON data saved to S3 bucket %s with key %s", s3_bucket, output_path)

    flattened_data = flatten_boe_data(data)
    df = pd.DataFrame(flattened_data)

    logger.info("DataFrame created with %d rows and %d columns", df.shape[0], df.shape[1])

    csv_output_dir = "output_csv"
    csv_output_file = f"boe_data_{date_str}.csv"
    csv_output_path = os.path.join(csv_output_dir, csv_output_file)

    if mode == "local":
        os.makedirs(csv_output_dir, exist_ok=True)
        df.to_csv(csv_output_path, index=False, encoding='utf-8', sep='|')
        logger.info("CSV data saved to %s", csv_output_path)

    elif mode == "lambda":
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8', sep='|')
        save_to_s3(
            body=csv_buffer.getvalue(),
            bucket=s3_bucket,
            key=csv_output_path,
            content_type='text/csv'
        )
        logger.info("CSV data saved to S3 bucket %s with key %s", s3_bucket, csv_output_path)

    return df


def save_to_s3(body, bucket, key, content_type=None):
    """
    Save the given body to an S3 bucket with the specified key.

    Args:
        body (str): The content to save.
        bucket (str): The name of the S3 bucket.
        key (str): The key under which to save the content.
        content_type (str, optional): The content type of the file. Defaults to None.
    """
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType=content_type
    )
    logger.info("File successfully uploaded to S3: s3://%s/%s", bucket, key)
