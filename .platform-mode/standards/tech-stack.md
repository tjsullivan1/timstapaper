# Tech Stack

## Context

Global tech stack defaults for infrastructure/platform projects based from this repo, overridable in project-specific `.platform-mode/product/tech-stack.md`.

## Infrastructure & Platform

- Infrastructure as Code: Terraform
- Scripting Language: Bash
- Enterprise Source Control as a Service: GitHub
- CI/CD Platform: GitHub Actions
- CI/CD Trigger: Push to main/staging branches
- Tests: Run before deployment
- Production Environment: main branch
- Staging Environment: staging branch
- Primary Cloud Provider: Microsoft Azure
- Application Hosting: Azure Kubernetes Service
- Hosting Region: Primary region based on user/project requirements - User/Environment Defined
- API Documentation: OpenAPI/Swagger with Azure API Management
- Local Development: Docker, Docker Compose, Dev Containers

## Monitoring & Observability

- Application Monitoring: Azure Application Insights
- Logging: Azure Monitor Logs
- Metrics & Alerting: Azure Monitor
- Error Tracking: Azure Application Insights

## Security & Compliance

- Authentication/Authorization: Azure Active Directory
- Secret Management: Azure Key Vault
- Code Security Scanning: GitHub Advanced Security
- Container Security: Azure Defender for Containers

## Communication & Collaboration

- Project Management: GitHub Projects

## Development Practices

- Code Review Process: Pull Request reviews
- Branching Strategy: GitHub Flow
- Deployment Strategy: TBD - Project Specific (Blue-green, rolling updates, canary releases)
- Environment Promotion: dev → staging → production pipeline

## Azure-Specific Services

- Container Orchestration: Azure Kubernetes Service
- Container Registry: Azure Container Registry
- API Gateway: Azure API Management
- Identity Provider: Azure Active Directory (Aka. Microsoft Entra)
- Networking: Azure Virtual Network, Azure Load Balancer