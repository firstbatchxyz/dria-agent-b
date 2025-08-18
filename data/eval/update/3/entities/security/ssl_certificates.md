# SSL Certificate Management - Phoenix Production

## Certificate Overview
- **Certificate ARN**: arn:aws:acm:us-east-1:123456789012:certificate/abcd1234-ef56-7890-abcd-1234567890ab
- **Domain**: *.phoenixcommerce.com
- **Certificate Authority**: Amazon Certificate Manager (ACM)
- **Validation Method**: DNS validation
- **Issued Date**: March 15, 2024
- **Expiration Date**: March 15, 2025

## Certificate Details
Wildcard SSL certificate covering all subdomains of the Phoenix e-commerce platform. The certificate uses RSA-2048 encryption with SHA-256 signature algorithm and supports TLS 1.2 and 1.3 protocols. Automatic renewal is enabled through ACM with DNS validation records maintained in Route 53. The certificate is deployed across multiple AWS services including Application Load Balancer, CloudFront distributions, and API Gateway endpoints.

## Domain Coverage
- **Primary Domain**: phoenixcommerce.com
- **Subdomains**: www.phoenixcommerce.com, api.phoenixcommerce.com, admin.phoenixcommerce.com
- **Staging Environment**: staging.phoenixcommerce.com
- **Development Environment**: dev.phoenixcommerce.com

## Validation Records
- **DNS Record Type**: CNAME
- **Validation Status**: Success (all domains validated)
- **Route 53 Hosted Zone**: Z1234567890ABC
- **Auto-renewal**: Enabled (90 days before expiration)

## Certificate Usage
- **Load Balancer**: phoenix-prod-alb (Primary listener port 443)
- **CloudFront**: 3 distributions using this certificate
- **API Gateway**: Phoenix REST API and GraphQL endpoints

## Monitoring & Compliance
- **Certificate Transparency**: Logged in CT logs (Google, Cloudflare, DigiCert)
- **Expiration Alerts**: CloudWatch alarms set for 60-day and 30-day warnings
- **Compliance Standards**: Meets PCI DSS requirements for data transmission security

## DNS Validation Records
- **Route 53 Configuration**: CNAME records for domain ownership verification automatically managed through hosted zone integration. [[dns/route53_configuration.md]]