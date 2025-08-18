# AWS Production Environment - Project Phoenix

## Infrastructure Overview
- **Environment Name**: Phoenix Production Environment
- **Cloud Provider**: Amazon Web Services (AWS)
- **Region**: us-east-1 (Primary), us-west-2 (DR)
- **Go-Live Date**: June 15, 2024
- **Compliance**: SOC 2 Type II, PCI DSS Level 1

## Architecture Summary
Multi-tier cloud-native architecture supporting high-availability e-commerce operations. The infrastructure utilizes containerized microservices deployed across multiple availability zones with auto-scaling capabilities. Load balancing distributes traffic across application instances with Redis caching layer for optimal performance. PostgreSQL RDS handles transactional data while S3 manages static assets and backups.

## Resource Allocation
- **Compute**: 24 EC2 instances (mix of t3.large and c5.xlarge)
- **Storage**: 2TB RDS PostgreSQL, 500GB Redis ElastiCache
- **CDN**: CloudFront distribution with 50+ edge locations
- **Monitoring**: CloudWatch with custom dashboards and alerting

## Security & Compliance
- **Network**: VPC with private subnets, NAT gateways, and security groups
- **Access Control**: IAM roles with least-privilege principles
- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Backup Strategy**: Automated daily snapshots with 30-day retention

## Network Configuration
- **Load Balancer**: Application Load Balancer distributing traffic to container instances and managing SSL termination. [[networking/alb_configuration.md]]