# Production Deployment Guide
## AWS Infrastructure Overview

**Environment:** Production (us-east-1 primary, us-west-2 failover)

**Architecture:** Microservices with containerized deployment

**Scaling Strategy:** Auto-scaling based on CPU/memory usage and request volume

## Deployment Prerequisites

**Required AWS Services:**
- ECS (Elastic Container Service) for application hosting
- RDS MongoDB Atlas integration for database
- CloudFront CDN for static asset delivery
- Route 53 for DNS management
- ALB (Application Load Balancer) for traffic distribution

**Security Requirements:**
- SSL certificates via AWS Certificate Manager
- VPC with private/public subnet configuration
- IAM roles with least-privilege access
- Secrets Manager for environment variables

## Production Deployment Steps

### 1. Infrastructure Setup
```bash
# Deploy infrastructure using Terraform
cd infrastructure/terraform
terraform init
terraform plan -var-file=\"prod.tfvars\"
terraform apply
```

### 2. Container Registry Setup
```bash
# Build and push Docker images
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin
docker build -t kankun-backend ./backend
docker tag kankun-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/kankun-backend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/kankun-backend:latest
```

### 3. ECS Service Deployment
```bash
# Update ECS services
aws ecs update-service --cluster kankun-prod --service kankun-backend-service --force-new-deployment
aws ecs wait services-stable --cluster kankun-prod --services kankun-backend-service
```

## Auto-Scaling Configuration

**Target Scaling Metrics:**
- CPU Utilization: Scale out at 70%, scale in at 30%
- Memory Utilization: Scale out at 80%
- Request Count: Scale out at 1000 requests/minute per instance

**Scaling Limits:**
- Minimum instances: 2
- Maximum instances: 10
- Scale-out cooldown: 300 seconds
- Scale-in cooldown: 600 seconds

## Environment Variables

**Production Secrets (AWS Secrets Manager):**
```json
{
  \"DATABASE_URL\": \"mongodb+srv://prod-cluster\",
  \"JWT_SECRET\": \"generated-secure-secret\",
  \"GOOGLE_MAPS_API_KEY\": \"production-api-key\",
  \"REDIS_URL\": \"elasticache-cluster-endpoint\",
  \"SENTRY_DSN\": \"production-sentry-url\"
}
```

## Monitoring & Alerting

**CloudWatch Alarms:**
- High error rate (>5% for 5 minutes)
- High response time (>2s average for 5 minutes)
- Low disk space (<20% remaining)

**Health Checks:**
- ALB health check: `/api/health` endpoint
- ECS health check: Container restart on failure
- Database connectivity: Connection pool monitoring

## Rollback Procedures

**Automated Rollback Triggers:**
- Error rate exceeds 10% for 2 consecutive minutes
- Health check failures for 3 consecutive checks

**Manual Rollback:**
```bash
# Rollback to previous task definition
aws ecs update-service --cluster kankun-prod --service kankun-backend-service --task-definition kankun-backend:PREVIOUS_REVISION
```

## SSL & Security

**Certificate Management:** Auto-renewal via AWS Certificate Manager

**Security Headers:** Implemented via CloudFront and ALB

**WAF Configuration:** Protection against common attacks and rate limiting