# Function: Triggered by EventBridge every minute. 
# It generates 50 random stock CSV files and uploads them to the stocks/ folder in your S3 bucket.

import json
import boto3
import csv
import io
import random
import time
from datetime import datetime

# Configuration based on your README
s3_client = boto3.client('s3')
BUCKET_NAME = 'project-14-bucket-shaheer'

def lambda_handler(event, context):
    print("Starting CSV generation batch...")
    
    tickers = ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'TSLA']
    
    # Generate 50 files as per requirements
    for i in range(50):
        ticker = random.choice(tickers)
        price = round(random.uniform(100, 500), 2)
        volume = random.randint(1000, 50000)
        timestamp = datetime.now().isoformat()
        
        # Create CSV content in memory
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['Ticker', 'Price', 'Volume', 'Timestamp'])
        writer.writerow([ticker, price, volume, timestamp])
        
        # Define file key: stocks/ prefix is required
        file_name = f"stocks/{ticker}_{int(time.time())}_{i}.csv"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=csv_buffer.getvalue()
        )
        
    return {
        'statusCode': 200,
        'body': json.dumps(f"Generated and uploaded 50 files to {BUCKET_NAME}")
    }