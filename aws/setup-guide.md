# AWS Infrastructure Setup Guide

This guide walks you through setting up the AWS infrastructure for deploying the Legacy Code Modernizer to Fargate.

## Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions
- Docker installed locally

## Step 1: Create IAM Roles

### Task Execution Role

This role is used by ECS to pull images and write logs.

```bash
# Create trust policy for ECS
cat > ecs-task-execution-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://ecs-task-execution-trust-policy.json

# Attach AWS managed policy
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### Task Role

This role is used by the application to access AWS services (Bedrock, etc.).

```bash
# Create trust policy
cat > ecs-task-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name legacy-code-modernizer-task-role \
  --assume-role-policy-document file://ecs-task-trust-policy.json

# Create and attach custom policy
aws iam create-policy \
  --policy-name legacy-code-modernizer-policy \
  --policy-document file://aws/iam-policy.json

# Get the policy ARN
POLICY_ARN=$(aws iam list-policies \
  --query 'Policies[?PolicyName==`legacy-code-modernizer-policy`].Arn' \
  --output text)

# Attach the policy
aws iam attach-role-policy \
  --role-name legacy-code-modernizer-task-role \
  --policy-arn $POLICY_ARN
```

## Step 2: Enable Bedrock Model Access

```bash
# List available Bedrock models
aws bedrock list-foundation-models \
  --region ap-southeast-2 \
  --query 'modelSummaries[?contains(modelId, `claude`)].{ID:modelId,Name:modelName}' \
  --output table

# Request access to Claude 3.5 Sonnet (if not already enabled)
# This must be done via AWS Console:
# 1. Go to AWS Bedrock console
# 2. Navigate to "Model access"
# 3. Request access to "Claude 3.5 Sonnet v2"
```

## Step 3: Create VPC Resources (Optional but Recommended)

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=legacy-code-modernizer-vpc}]' \
  --query 'Vpc.VpcId' \
  --output text)

# Create subnets
SUBNET1_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone ap-southeast-2a \
  --query 'Subnet.SubnetId' \
  --output text)

SUBNET2_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone ap-southeast-2b \
  --query 'Subnet.SubnetId' \
  --output text)

# Create internet gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

aws ec2 attach-internet-gateway \
  --vpc-id $VPC_ID \
  --internet-gateway-id $IGW_ID

# Create route table
ROUTE_TABLE_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' \
  --output text)

aws ec2 create-route \
  --route-table-id $ROUTE_TABLE_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

aws ec2 associate-route-table \
  --subnet-id $SUBNET1_ID \
  --route-table-id $ROUTE_TABLE_ID

aws ec2 associate-route-table \
  --subnet-id $SUBNET2_ID \
  --route-table-id $ROUTE_TABLE_ID

# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name legacy-code-modernizer-sg \
  --description "Security group for Legacy Code Modernizer" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

# Allow outbound traffic (needed for Bedrock API calls)
aws ec2 authorize-security-group-egress \
  --group-id $SG_ID \
  --ip-permissions IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges='[{CidrIp=0.0.0.0/0}]'
```

## Step 4: Create CloudWatch Log Group

```bash
aws logs create-log-group \
  --log-group-name /ecs/legacy-code-modernizer \
  --region ap-southeast-2
```

## Step 5: Create Secrets Manager Secret (Optional)

If you prefer to store AWS credentials in Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name legacy-code-modernizer/aws-credentials \
  --description "AWS credentials for Legacy Code Modernizer" \
  --secret-string '{
    "AWS_ACCESS_KEY_ID": "your-access-key",
    "AWS_SECRET_ACCESS_KEY": "your-secret-key"
  }' \
  --region ap-southeast-2
```

## Step 6: Create ECS Cluster

```bash
aws ecs create-cluster \
  --cluster-name legacy-code-modernizer-cluster \
  --region ap-southeast-2
```

## Step 7: Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name legacy-code-modernizer \
  --region ap-southeast-2
```

## Step 8: Deploy Application

Now you can use the deployment script:

```bash
./deploy.sh
```

## Step 9: Create ECS Service

```bash
# Get the latest task definition ARN
TASK_DEF_ARN=$(aws ecs describe-task-definition \
  --task-definition legacy-code-modernizer \
  --region ap-southeast-2 \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

# Create service
aws ecs create-service \
  --cluster legacy-code-modernizer-cluster \
  --service-name legacy-code-modernizer-service \
  --task-definition $TASK_DEF_ARN \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[$SUBNET1_ID,$SUBNET2_ID],
    securityGroups=[$SG_ID],
    assignPublicIp=ENABLED
  }" \
  --region ap-southeast-2
```

## Verify Deployment

```bash
# Check service status
aws ecs describe-services \
  --cluster legacy-code-modernizer-cluster \
  --services legacy-code-modernizer-service \
  --region ap-southeast-2

# View logs
aws logs tail /ecs/legacy-code-modernizer --follow
```

## Cleanup

To remove all resources:

```bash
# Delete service
aws ecs update-service \
  --cluster legacy-code-modernizer-cluster \
  --service legacy-code-modernizer-service \
  --desired-count 0 \
  --region ap-southeast-2

aws ecs delete-service \
  --cluster legacy-code-modernizer-cluster \
  --service legacy-code-modernizer-service \
  --region ap-southeast-2

# Delete cluster
aws ecs delete-cluster \
  --cluster legacy-code-modernizer-cluster \
  --region ap-southeast-2

# Delete ECR repository
aws ecr delete-repository \
  --repository-name legacy-code-modernizer \
  --force \
  --region ap-southeast-2

# Delete VPC resources (if created)
# ... (security groups, subnets, igw, vpc)

# Delete log group
aws logs delete-log-group \
  --log-group-name /ecs/legacy-code-modernizer \
  --region ap-southeast-2
```

## Cost Optimization Tips

1. **Use Fargate Spot** for non-production workloads (up to 70% savings)
2. **Adjust CPU/Memory** based on actual usage
3. **Enable auto-scaling** based on metrics
4. **Use CloudWatch Logs retention** policy to reduce storage costs
5. **Consider Reserved Capacity** for production workloads

## Monitoring

Set up CloudWatch alarms:

```bash
# CPU utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name legacy-code-modernizer-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=legacy-code-modernizer-service Name=ClusterName,Value=legacy-code-modernizer-cluster

# Memory utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name legacy-code-modernizer-high-memory \
  --alarm-description "Alert when memory exceeds 80%" \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=legacy-code-modernizer-service Name=ClusterName,Value=legacy-code-modernizer-cluster
```
