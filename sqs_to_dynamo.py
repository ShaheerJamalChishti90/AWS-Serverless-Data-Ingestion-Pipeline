# Function: Triggered by the SQS queue.
# It parses the SQS message (which contains the S3 event), downloads the file, and writes it to DynamoDB.

import json
import boto3
import csv
import io

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Replace with your actual DynamoDB table name
TABLE_NAME = 'StockData'

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    
    # Loop through SQS messages (Batch size is usually 1-10)
    for record in event['Records']:
        try:
            # SQS wraps the S3 event in the 'body' string
            sqs_body = json.loads(record['body'])
            
            # Navigate to the S3 event details
            if 'Records' in sqs_body:
                s3_event = sqs_body['Records'][0]
                bucket_name = s3_event['s3']['bucket']['name']
                file_key = s3_event['s3']['object']['key']
                
                print(f"Processing file: {file_key} from {bucket_name}")
                
                # Download CSV file from S3
                response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
                file_content = response['Body'].read().decode('utf-8')
                
                # Parse CSV data
                csv_reader = csv.DictReader(io.StringIO(file_content))
                
                # Write to DynamoDB
                for row in csv_reader:
                    table.put_item(
                        Item={
                            'PK': row['Ticker'],      # Partition Key
                            'SK': row['Timestamp'],   # Sort Key (optional)
                            'Price': row['Price'],
                            'Volume': row['Volume'],
                            'SourceFile': file_key
                        }
                    )
            else:
                print("Skipping non-S3 event message")
                
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            # If this fails, SQS will retry and eventually move to DLQ
            raise e
            
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }