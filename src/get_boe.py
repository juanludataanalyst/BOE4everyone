from process_boe import flatten_boe_data
import os
import json
from datetime import datetime
import requests
import pandas as pd
import boto3
from io import StringIO

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
    # Check if kwards are provided
    if kwards:
        if "s3_bucket" in kwards:
            s3_bucket = kwards["s3_bucket"]
            mode = "lambda"
        

    # Check if date and data are provided
    if data and date:
        date_str = date

    elif data is None:
        if date is None:
            # If no date is provided, use today's date
            # Format date as YYYYMMDD
            date_str = datetime.today().strftime('%Y%m%d')
        else:
            date_str = date
         
        # API request details
        url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{date_str}"
        headers = {"Accept": "application/json"}
        
        # Make the API request
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
            
            data = response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from BOE API: {e}")
            return pd.DataFrame()
        
        else:

            # Save the response to a JSON file
            json_output_dir = "output_json"
            output_file = f"boe_data_{date_str}.json"
            output_path = os.path.join("output_json", output_file)

            if mode == "local":
                os.makedirs(json_output_dir, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print(f"Data saved to {output_path}")

            elif mode == "lambda":
                # Save the response to S3
                save_to_s3(
                    body=json.dumps(data),
                    bucket = s3_bucket,
                    key = output_path,
                    content_type='application/json'
                )
                print(f"Data saved to S3 bucket {s3_bucket} with key {output_path}")

    # Process the nested structure
    flattened_data = flatten_boe_data(data)
    
    # Convert to DataFrame
    df = pd.DataFrame(flattened_data)

    # Save the DataFrame to a CSV file
    csv_output_dir = "output_csv"
    csv_output_file = f"boe_data_{date_str}.csv"
    csv_output_path = os.path.join(csv_output_dir, csv_output_file)

    if mode == "local":
        os.makedirs(csv_output_dir, exist_ok=True)
        df.to_csv(csv_output_path, index=False, encoding='utf-8', sep='|')
        print(f"Data saved to {csv_output_path}")

    elif mode == "lambda":
        # Save the DataFrame to S3
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8', sep='|')
        save_to_s3(
            body=csv_buffer.getvalue(),
            bucket = s3_bucket,
            key = csv_output_path,
            content_type='text/csv'
        )
        print(f"Data saved to S3 bucket {s3_bucket} with key {csv_output_path}")
    
    return df


def save_to_s3(body, bucket, key, content_type = None):
    """
    Save the given body to an S3 bucket with the specified key.
    This is aimed to be usd when running the function from AWS Lambda.
    
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
        ContentType=content_type)
