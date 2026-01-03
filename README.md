# AWS Serverless Data Ingestion Pipeline

## Project Overview

This project implements a fully automated, event-driven data ingestion pipeline on AWS. It demonstrates a serverless architecture that generates synthetic stock market data, buffers it using a queue for decoupling, and ingests it into a NoSQL database for real-time storage.

The primary goal of this architecture is to demonstrate **decoupling** using Amazon SQS (Simple Queue Service) to handle high-throughput data ingestion without overloading the downstream consumer or database.

## Architecture

The pipeline follows this data flow:

1. **EventBridge:** Triggers a producer Lambda function on a scheduled interval (e.g., every 1 minute).
2. **Generator Lambda:** Generates batch CSV files containing stock market data and uploads them to an S3 bucket.
3. **Amazon S3:** Stores the raw CSV files. An event notification is triggered upon file creation.
4. **Amazon SQS:** Receives the S3 event notification. Acts as a buffer to decouple the storage layer from the processing layer.
5. **Consumer Lambda:** Polls the SQS queue, retrieves the S3 event details, downloads the CSV file, and parses the data.
6. **Amazon DynamoDB:** Stores the parsed records for analysis.

## Tech Stack

* **Cloud Provider:** AWS
* **Compute:** AWS Lambda (Python 3.9+)
* **Storage:** Amazon S3 (Object Storage), Amazon DynamoDB (NoSQL Database)
* **Messaging:** Amazon SQS (Standard Queue)
* **Orchestration:** Amazon EventBridge (Scheduler)
* **Language:** Python (Boto3 SDK)

## Repository Structure

```text
/
├── data_to_s3.py         # Generator Lambda function code
├── sqs_to_dynamo.py      # Consumer Lambda function code
├── architecture_diagram.png
└── README.md

```

## Prerequisites

* An active AWS Account.
* Basic understanding of IAM roles and policies.
* Python 3.x installed locally (for testing scripts).

## Deployment Guide

### Phase 1: Infrastructure Setup

**1. DynamoDB Table**

* Create a table named `StockData`.
* **Partition Key (PK):** `PK` (String) - Used for the Stock Ticker.
* **Sort Key (SK):** `SK` (String) - Used for the Timestamp.
* Leave read/write capacity settings at default (On-demand is recommended for testing).

**2. Amazon SQS Queue**

* Create a Standard Queue named `StockQueue`.
* Note the **Queue ARN** and **Queue URL** for later configuration.
* Keep default visibility timeout settings initially (adjust to 1 minute if processing large files).

**3. Amazon S3 Bucket**

* Create a unique S3 bucket (e.g., `your-project-stock-data`).
* Block all public access (best practice).

### Phase 2: IAM Configuration

**Generator Role (For data_to_s3.py)**
Create an IAM Role with the following permissions:

* `AmazonS3FullAccess` (Or strictly scoped `PutObject` permission for the specific bucket).
* `CloudWatchLogsFullAccess` (For logging).

**Consumer Role (For sqs_to_dynamo.py)**
Create an IAM Role with the following permissions:

* `AmazonS3ReadOnlyAccess` (To download CSVs).
* `AmazonDynamoDBFullAccess` (To write records).
* `AWSLambdaSQSQueueExecutionRole` (To poll the queue).

### Phase 3: Lambda Functions

**Function 1: Generator Lambda**

* **Name:** `GeneratorLambda`
* **Runtime:** Python 3.9
* **Code:** Copy content from `data_to_s3.py`.
* **Environment Variables:** Update the `BUCKET_NAME` variable in the code to match your S3 bucket.
* **Configuration:** Increase timeout to 1 minute to allow time for generating 50 files.

**Function 2: Consumer Lambda**

* **Name:** `ConsumerLambda`
* **Runtime:** Python 3.9
* **Code:** Copy content from `sqs_to_dynamo.py`.
* **Environment Variables:** Update the `TABLE_NAME` variable in the code if different from `StockData`.

### Phase 4: Event Triggers & Wiring

**1. S3 to SQS Permission**
Update the SQS Access Policy to allow the S3 bucket to send messages. Replace `<your-bucket-name>` and `<your-queue-arn>` in the policy below:

```json
{
  "Effect": "Allow",
  "Principal": { "Service": "s3.amazonaws.com" },
  "Action": "sqs:SendMessage",
  "Resource": "<your-queue-arn>",
  "Condition": {
    "ArnLike": { "aws:SourceArn": "arn:aws:s3:::<your-bucket-name>" }
  }
}

```

**2. S3 Event Notification**

* Go to S3 Bucket Properties -> Event Notifications.
* Create an event for `All object create events`.
* **Prefix:** `stocks/`
* **Destination:** SQS Queue (`StockQueue`).

**3. Consumer Trigger**

* Go to the `ConsumerLambda` function.
* Add Trigger -> SQS.
* Select `StockQueue`.

**4. Generator Trigger (EventBridge)**

* Go to the `GeneratorLambda` function.
* Add Trigger -> EventBridge (CloudWatch Events).
* Create a new rule with Schedule Expression: `rate(1 minute)`.

## Usage & Testing

1. **Manual Test:** Navigate to the `GeneratorLambda` console and click **Test**. This will execute the script once.
2. **Verify S3:** Check your bucket for a `stocks/` folder containing CSV files.
3. **Verify SQS:** Check the monitoring tab in SQS to see "Messages Received" spikes.
4. **Verify DynamoDB:** Scan the `StockData` table to confirm data rows have been inserted.
