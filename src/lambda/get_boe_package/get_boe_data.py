import json
import boto3
import requests
from datetime import datetime
import os

def lambda_handler(event, context):
    """
    AWS Lambda function that fetches the BOE data for the current day
    and stores it in an S3 bucket.
    
    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object
        
    Returns:
        dict: Response containing status and information about the processed data
    """
    # Get the current date in YYYYMMDD format
    today = datetime.now().strftime('%Y%m%d')
    
    # Get environment variables
    s3_bucket = os.environ.get('S3_BUCKET_NAME', 'boe-facil')
    json_folder = os.environ.get('JSON_FOLDER', 'json')
    
    # Construct BOE API URL for the current date
    boe_url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{today}"
    headers = {"Accept": "application/json"}
    
    try:
        # Fetch data from BOE API
        response = requests.get(boe_url, headers=headers)
        
        # Check if the response is successful
        if response.status_code != 200:
            error_message = f"Failed to fetch BOE data. Status code: {response.status_code}"
            print(error_message)
            return {
                'statusCode': response.status_code,
                'body': json.dumps({
                    'message': error_message,
                    'date': today
                })
            }
        
        # Parse the response as JSON
        boe_data = response.json()
        
        # Create S3 client
        s3_client = boto3.client('s3')
        
        # Define the S3 key (file path in the bucket)
        s3_key = f"{json_folder}/boe_data_{today}.json"
        
        # Upload the JSON data to S3
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=json.dumps(boe_data),
            ContentType='application/json'
        )
        
        print(f"BOE data for {today} uploaded to s3://{s3_bucket}/{s3_key}")
        
        # Invoke the flatten_boe_data Lambda function
        #lambda_client = boto3.client('lambda')
        #lambda_client.invoke(
        #    FunctionName=os.environ.get('FLATTEN_FUNCTION_NAME', 'flatten_boe_data'),
        #    InvocationType='Event',  # Asynchronous invocation
        #    Payload=json.dumps({
        #        's3_bucket': s3_bucket,
        #        's3_key': s3_key,
        #        'date': today
        #    })
        #)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'BOE data successfully fetched and stored in S3',
                'date': today,
                's3_bucket': s3_bucket,
                's3_key': s3_key,
                'next_step': 'Flatten function invoked'
            })
        }
        
    except Exception as e:
        error_message = f"Error processing BOE data: {str(e)}"
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': error_message,
                'date': datetime.now().strftime('%Y%m%d')
            })
        }