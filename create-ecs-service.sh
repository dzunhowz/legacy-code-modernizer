#!/bin/bash
# Create ECS Service with Fargate

set -e

# Configuration
AWS_REGION=${AWS_REGION:-ap-southeast-2}
ECS_CLUSTER_NAME="legacy-code-modernizer-cluster"
ECS_SERVICE_NAME="legacy-code-modernizer-service"
TASK_DEFINITION_ARN="arn:aws:ecs:ap-southeast-2:922523344160:task-definition/legacy-code-modernizer:1"

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

# Check if required parameters are set
if [ -z "$VPC_ID" ]; then
    echo_error "VPC_ID environment variable is not set."
    echo_info "Please set it: export VPC_ID=vpc-xxxxxxxxx"
    exit 1
fi

if [ -z "$SUBNET_IDS" ]; then
    echo_error "SUBNET_IDS environment variable is not set."
    echo_info "Please set it: export SUBNET_IDS=subnet-xxxxx,subnet-yyyyy"
    echo_info "Use at least 2 subnets in different availability zones for high availability."
    exit 1
fi

if [ -z "$SECURITY_GROUP_ID" ]; then
    echo_warn "SECURITY_GROUP_ID not set. Creating a default security group..."
    
    # Create security group
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --group-name legacy-code-modernizer-sg \
        --description "Security group for Legacy Code Modernizer" \
        --vpc-id $VPC_ID \
        --region $AWS_REGION \
        --query 'GroupId' \
        --output text)
    
    echo_info "Created security group: $SECURITY_GROUP_ID"
    
    # Add ingress rule for port 8080 (MCP server)
    aws ec2 authorize-security-group-ingress \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 8080 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION
    
    echo_info "Added ingress rule for port 8080"
fi

echo_info "Creating ECS service..."
echo_info "  Cluster: $ECS_CLUSTER_NAME"
echo_info "  Service: $ECS_SERVICE_NAME"
echo_info "  Task Definition: $TASK_DEFINITION_ARN"
echo_info "  VPC: $VPC_ID"
echo_info "  Subnets: $SUBNET_IDS"
echo_info "  Security Group: $SECURITY_GROUP_ID"

# Create the service
aws ecs create-service \
    --cluster $ECS_CLUSTER_NAME \
    --service-name $ECS_SERVICE_NAME \
    --task-definition $TASK_DEFINITION_ARN \
    --desired-count 1 \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
    --region $AWS_REGION

echo_info "Service created successfully!"
echo_info ""
echo_info "To check service status:"
echo_info "  aws ecs describe-services --cluster $ECS_CLUSTER_NAME --services $ECS_SERVICE_NAME --region $AWS_REGION"
echo_info ""
echo_info "To view service logs:"
echo_info "  aws logs tail /ecs/legacy-code-modernizer --follow --region $AWS_REGION"
