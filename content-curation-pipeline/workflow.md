# AWS Deployment Workflow for Content Curation Pipeline

This document outlines the steps and infrastructure needed to deploy the content curation pipeline to AWS using Infrastructure as Code (IaC).

## Architecture Overview

```
┌────────────────┐    ┌───────────────┐    ┌────────────────┐    ┌─────────────────┐
│                │    │               │    │                │    │                 │
│  EventBridge   │───▶│  Lambda/      │───▶│  Step          │───▶│  Lambda         │
│  Scheduler     │    │  Function     │    │  Functions     │    │  Workers        │
│                │    │  Trigger      │    │                │    │                 │
└────────────────┘    └───────────────┘    └────────────────┘    └────────┬────────┘
                                                                          │
                 ┌──────────────────────────────────────────────────────┐ │
                 │                                                      │ │
                 ▼                                                      │ ▼
        ┌─────────────────┐    ┌───────────────┐    ┌────────────────┐ │ ┌─────────────────┐
        │                 │    │               │    │                │ │ │                 │
        │  S3             │◀───│  Lambda       │◀───│  Qdrant Cloud  │◀─┘ │  ElastiCache    │
        │  Object Storage │    │  Results      │    │  Vector Store  │    │  Redis          │
        │                 │    │  Processor    │    │                │    │                 │
        └─────────────────┘    └───────────────┘    └────────────────┘    └─────────────────┘
```

## Infrastructure Components

1. **AWS Lambda**: Serverless compute for pipeline execution
2. **AWS Step Functions**: Orchestration of pipeline steps
3. **Amazon S3**: Storage for content, results, and artifacts
4. **Amazon ElastiCache for Redis**: URL caching and temporary storage
5. **Qdrant Cloud (AWS Region)**: Managed vector database
6. **Amazon EventBridge**: Scheduling daily runs
7. **AWS IAM**: Identity and access management
8. **AWS CloudWatch**: Monitoring and logging
9. **AWS Secrets Manager**: Managing API keys and credentials

## Deployment Workflow

### Phase 1: Infrastructure Setup

1. **Create Terraform Configuration Files**
   - Create `main.tf`, `variables.tf`, `outputs.tf`
   - Define providers and backend configuration
   - Setup remote state storage in S3
   - Define resource modules for each component

2. **Setup IAM Roles and Policies**
   - Create service roles for Lambda functions
   - Define least-privilege policies
   - Setup cross-service permissions

3. **Configure Storage Resources**
   - Create S3 buckets for:
     - Pipeline results
     - Intermediate content storage
     - Deployment artifacts
   - Setup appropriate lifecycle policies and access controls

4. **Setup Redis Cache**
   - Deploy ElastiCache Redis cluster
   - Configure security groups and subnet groups
   - Setup parameter groups for optimal performance

5. **Configure Qdrant Cloud**
   - Create Qdrant Cloud account and deploy instance in matching AWS region
   - Setup authentication and connection details
   - Store connection information in AWS Secrets Manager

### Phase 2: Application Deployment

1. **Containerize Application**
   - Create Dockerfile for the pipeline
   - Include all dependencies
   - Optimize container size and startup time

2. **Setup CI/CD Pipeline**
   - Configure GitHub Actions or AWS CodePipeline
   - Automate testing, building, and deployment
   - Setup approval gates for production changes

3. **Deploy Lambda Functions**
   - Create Lambda functions using container images:
     - Pipeline trigger function
     - URL processing function
     - Results processing function
   - Configure memory and timeout settings
   - Setup environment variables and secrets

4. **Configure Step Functions Workflow**
   - Create state machine definition for pipeline orchestration
   - Define error handling and retry logic
   - Setup input/output processing between states

5. **Setup Scheduler**
   - Configure EventBridge rule for daily execution
   - Define target and input parameters
   - Setup monitoring for execution failures

### Phase 3: Monitoring and Operations

1. **Setup CloudWatch Dashboards**
   - Create custom dashboards for pipeline metrics
   - Configure alarms for error rates and latency
   - Setup log groups and filters

2. **Configure Alerting**
   - Setup SNS topics for alerting
   - Configure alert routing based on severity
   - Implement escalation procedures

3. **Implement Cost Controls**
   - Setup AWS Budgets
   - Configure resource tagging strategy
   - Implement auto-scaling policies

## Terraform Modules Structure

```
terraform/
├── main.tf               # Main configuration
├── variables.tf          # Input variables
├── outputs.tf            # Output values
├── modules/
│   ├── lambda/           # Lambda function resources
│   ├── step-functions/   # Step Functions state machine
│   ├── storage/          # S3 buckets and policies
│   ├── cache/            # ElastiCache Redis configuration
│   ├── scheduler/        # EventBridge rules
│   ├── monitoring/       # CloudWatch resources
│   └── iam/              # IAM roles and policies
└── environments/
    ├── dev/              # Development environment config
    └── prod/             # Production environment config
```

## Implementation Tasks

### Week 1: Initial Setup
- [ ] Create GitHub repository for infrastructure code
- [ ] Setup AWS account and IAM users
- [ ] Initialize Terraform project
- [ ] Create basic infrastructure modules
- [ ] Setup remote state management

### Week 2: Core Infrastructure
- [ ] Implement S3 bucket provisioning
- [ ] Setup ElastiCache Redis cluster
- [ ] Configure Qdrant Cloud instance
- [ ] Create IAM roles and policies
- [ ] Setup secrets management

### Week 3: Application Deployment
- [ ] Containerize the pipeline application
- [ ] Create Lambda function resources
- [ ] Implement Step Functions state machine
- [ ] Setup EventBridge scheduler
- [ ] Configure environment variables

### Week 4: Testing and Optimization
- [ ] Implement end-to-end testing
- [ ] Configure CloudWatch monitoring
- [ ] Optimize Lambda performance
- [ ] Setup cost monitoring
- [ ] Document the deployment process

## Key Configuration Files

### Example `terraform/main.tf`

```hcl
provider "aws" {
  region = var.aws_region
}

terraform {
  backend "s3" {
    bucket = "skip-level-ai-terraform-state"
    key    = "non-agentic-pipeline/terraform.tfstate"
    region = "us-east-1"
  }
}

module "storage" {
  source = "./modules/storage"
  
  environment = var.environment
  bucket_name_prefix = "skip-level-ai-pipeline"
}

module "redis" {
  source = "./modules/cache"
  
  environment = var.environment
  vpc_id = var.vpc_id
  subnet_ids = var.subnet_ids
}

module "lambda_functions" {
  source = "./modules/lambda"
  
  environment = var.environment
  ecr_repository_url = var.ecr_repository_url
  s3_bucket = module.storage.bucket_name
  redis_endpoint = module.redis.endpoint
  qdrant_secrets_arn = var.qdrant_secrets_arn
}

module "step_functions" {
  source = "./modules/step-functions"
  
  environment = var.environment
  lambda_functions = module.lambda_functions.function_arns
}

module "scheduler" {
  source = "./modules/scheduler"
  
  environment = var.environment
  step_function_arn = module.step_functions.state_machine_arn
  schedule_expression = "cron(0 0 * * ? *)"  # Daily at midnight UTC
}

module "monitoring" {
  source = "./modules/monitoring"
  
  environment = var.environment
  lambda_functions = module.lambda_functions.function_names
  step_function_name = module.step_functions.state_machine_name
}
```

### Example Step Functions Definition

```json
{
  "Comment": "Non-Agentic Pipeline Workflow",
  "StartAt": "FetchURLs",
  "States": {
    "FetchURLs": {
      "Type": "Task",
      "Resource": "${fetch_urls_lambda_arn}",
      "Next": "ProcessURLs",
      "Retry": [
        {
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "HandleError"
        }
      ]
    },
    "ProcessURLs": {
      "Type": "Map",
      "ItemsPath": "$.urls",
      "Iterator": {
        "StartAt": "EvaluateURL",
        "States": {
          "EvaluateURL": {
            "Type": "Task",
            "Resource": "${evaluate_url_lambda_arn}",
            "End": true
          }
        }
      },
      "Next": "ProcessResults",
      "MaxConcurrency": 10
    },
    "ProcessResults": {
      "Type": "Task",
      "Resource": "${process_results_lambda_arn}",
      "Next": "SaveResults"
    },
    "SaveResults": {
      "Type": "Task",
      "Resource": "${save_results_lambda_arn}",
      "End": true
    },
    "HandleError": {
      "Type": "Task",
      "Resource": "${error_handler_lambda_arn}",
      "End": true
    }
  }
}
```

## Appendix: Helpful AWS CLI Commands

```bash
# Deploy Terraform infrastructure
terraform init
terraform plan -var-file=environments/dev/terraform.tfvars
terraform apply -var-file=environments/dev/terraform.tfvars

# Manually trigger Step Functions execution
aws stepfunctions start-execution \
  --state-machine-arn <state_machine_arn> \
  --input '{"query": "engineering career growth frameworks and evaluation criteria", "evaluation_method": "openai_browsing"}'

# Check Lambda logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/pipeline-evaluator \
  --filter-pattern "ERROR"

# Scale Redis cluster
aws elasticache increase-replica-count \
  --replication-group-id skip-level-redis \
  --apply-immediately \
  --new-replica-count 2
``` 