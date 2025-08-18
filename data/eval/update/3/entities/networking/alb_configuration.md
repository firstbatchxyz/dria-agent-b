# Application Load Balancer Configuration - Phoenix ALB

## Load Balancer Details
- **ALB Name**: phoenix-prod-alb
- **ARN**: arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/phoenix-prod-alb/1234567890abcdef
- **Scheme**: Internet-facing
- **IP Address Type**: IPv4
- **VPC**: vpc-0a1b2c3d4e5f67890

## Configuration Summary
Production Application Load Balancer handling HTTPS traffic distribution across containerized microservices. Configured with SSL termination using ACM certificates, health checks every 30 seconds, and sticky sessions for user authentication. The ALB routes traffic based on path patterns to appropriate target groups including web servers, API services, and admin interfaces. Cross-zone load balancing ensures even distribution across availability zones.

## Target Groups
- **Web Frontend**: phoenix-web-tg (Port 3000, 6 healthy targets)
- **API Services**: phoenix-api-tg (Port 8080, 8 healthy targets)  
- **Admin Panel**: phoenix-admin-tg (Port 3001, 2 healthy targets)
- **Health Check**: HTTP GET /health every 30s, 2 consecutive successes required

## Listener Rules
- **Port 443 (HTTPS)**: Primary listener with SSL certificate arn:aws:acm:us-east-1:123456789012:certificate/abcd1234-ef56-7890-abcd-1234567890ab
- **Port 80 (HTTP)**: Redirect to HTTPS
- **Path Routing**: /api/* → API services, /admin/* → Admin panel, /* → Web frontend

## Security & Monitoring
- **Security Groups**: sg-0123456789abcdef0 (Allow 80/443 from 0.0.0.0/0)
- **Access Logs**: Enabled to S3 bucket phoenix-alb-logs
- **CloudWatch Metrics**: Request count, response time, error rates tracked

## SSL Certificate Management
- **Certificate Authority**: AWS Certificate Manager with automatic renewal and domain validation status monitoring. [[security/ssl_certificates.md]]