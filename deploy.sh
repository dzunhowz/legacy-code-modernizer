#!/bin/bash
# Deploy script for AWS Fargate

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REPOSITORY_NAME="legacy-code-modernizer"
ECS_CLUSTER_NAME="legacy-code-modernizer-cluster"
ECS_SERVICE_NAME="legacy-code-modernizer-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
echo_info "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo_error "AWS CLI not found. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo_error "Docker not found. Please install it first."
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo_info "AWS Account ID: $AWS_ACCOUNT_ID"

# Create ECR repository if it doesn't exist
echo_info "Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION

# Get ECR repository URI
ECR_REPOSITORY_URI=$(aws ecr describe-repositories \
    --repository-names $ECR_REPOSITORY_NAME \
    --region $AWS_REGION \
    --query 'repositories[0].repositoryUri' \
    --output text)

echo_info "ECR Repository URI: $ECR_REPOSITORY_URI"

# Login to ECR
echo_info "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REPOSITORY_URI

# Build Docker image
echo_info "Building Docker image..."
docker build -t $ECR_REPOSITORY_NAME:latest .

# Tag image for ECR
echo_info "Tagging image..."
docker tag $ECR_REPOSITORY_NAME:latest $ECR_REPOSITORY_URI:latest

# Push image to ECR
echo_info "Pushing image to ECR..."
docker push $ECR_REPOSITORY_URI:latest

# Create or update task definition
echo_info "Updating ECS task definition..."
TASK_DEFINITION=$(cat fargate-task-definition.json | \
    sed "s/\${ECR_REPOSITORY_URI}/$ECR_REPOSITORY_URI/g" | \
    sed "s/\${AWS_ACCOUNT_ID}/$AWS_ACCOUNT_ID/g")

TASK_DEFINITION_ARN=$(echo $TASK_DEFINITION | \
    aws ecs register-task-definition \
        --cli-input-json file:///dev/stdin \
        --region $AWS_REGION \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)

echo_info "Task Definition ARN: $TASK_DEFINITION_ARN"

# Create ECS cluster if it doesn't exist
echo_info "Creating ECS cluster..."
aws ecs describe-clusters --clusters $ECS_CLUSTER_NAME --region $AWS_REGION 2>/dev/null || \
    aws ecs create-cluster --cluster-name $ECS_CLUSTER_NAME --region $AWS_REGION

# Update or create ECS service
echo_info "Updating ECS service..."
if aws ecs describe-services --cluster $ECS_CLUSTER_NAME --services $ECS_SERVICE_NAME --region $AWS_REGION --query 'services[0].serviceName' --output text 2>/dev/null | grep -q $ECS_SERVICE_NAME; then
    aws ecs update-service \
        --cluster $ECS_CLUSTER_NAME \
        --service $ECS_SERVICE_NAME \
        --task-definition $TASK_DEFINITION_ARN \
        --region $AWS_REGION \
        --force-new-deployment
    echo_info "Service updated successfully"
else
    echo_warn "Service does not exist. Please create it manually with appropriate VPC configuration."
    echo_warn "Use the following task definition ARN: $TASK_DEFINITION_ARN"
fi

echo_info "Deployment completed successfully!"
