#!/bin/bash

# AWS ECS Deployment Script for Vamshi Wake-up Calls
# This script builds and deploys the application to AWS Fargate

set -e

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="wakeupcalls-app"
ECS_CLUSTER="wakeupcalls-cluster"
ECS_SERVICE="wakeupcalls-service"
TASK_DEFINITION_FAMILY="wakeupcalls-app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting deployment of Vamshi Wake-up Calls...${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  AWS Account ID: ${AWS_ACCOUNT_ID}"
echo "  AWS Region: ${AWS_REGION}"
echo "  ECR Repository: ${ECR_URI}"
echo "  ECS Cluster: ${ECS_CLUSTER}"
echo "  ECS Service: ${ECS_SERVICE}"

# Step 1: Create ECR repository if it doesn't exist
echo -e "${YELLOW}🏗️  Creating ECR repository if it doesn't exist...${NC}"
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} || \
aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${AWS_REGION}

# Step 2: Login to ECR
echo -e "${YELLOW}🔐 Logging into ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

# Step 3: Build Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -t ${ECR_REPOSITORY}:latest .

# Step 4: Tag image for ECR
echo -e "${YELLOW}🏷️  Tagging image for ECR...${NC}"
docker tag ${ECR_REPOSITORY}:latest ${ECR_URI}:latest

# Step 5: Push image to ECR
echo -e "${YELLOW}📤 Pushing image to ECR...${NC}"
docker push ${ECR_URI}:latest

# Step 6: Update task definition with new image URI
echo -e "${YELLOW}📝 Updating task definition...${NC}"
sed "s|YOUR_ECR_REPOSITORY_URI|${ECR_URI}|g" aws-task-definition.json > aws-task-definition-updated.json
sed -i "s|YOUR_ACCOUNT_ID|${AWS_ACCOUNT_ID}|g" aws-task-definition-updated.json

# Step 7: Register new task definition
echo -e "${YELLOW}📋 Registering new task definition...${NC}"
TASK_DEFINITION_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://aws-task-definition-updated.json \
    --region ${AWS_REGION} \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "  New task definition: ${TASK_DEFINITION_ARN}"

# Step 8: Update ECS service
echo -e "${YELLOW}🔄 Updating ECS service...${NC}"
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --task-definition ${TASK_DEFINITION_ARN} \
    --region ${AWS_REGION}

# Step 9: Wait for deployment to complete
echo -e "${YELLOW}⏳ Waiting for deployment to complete...${NC}"
aws ecs wait services-stable \
    --cluster ${ECS_CLUSTER} \
    --services ${ECS_SERVICE} \
    --region ${AWS_REGION}

# Clean up
rm -f aws-task-definition-updated.json

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🎉 Vamshi Wake-up Calls is now running on AWS Fargate!${NC}"

# Get service URL (if using Application Load Balancer)
echo -e "${YELLOW}🌐 Service Information:${NC}"
aws ecs describe-services \
    --cluster ${ECS_CLUSTER} \
    --services ${ECS_SERVICE} \
    --region ${AWS_REGION} \
    --query 'services[0].loadBalancers[0].targetGroupArn' \
    --output text
