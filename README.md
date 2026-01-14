# Web Application Template

A comprehensive template repository for building and deploying web applications with modern DevOps practices.

## 🏗️ Repository Structure

```
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # Continuous Integration pipeline
│   │   ├── infra-plan-apply.yml      # Infrastructure deployment
│   │   └── deploy-webapp.yml         # Application deployment
│   └── dependabot.yml                # Dependency updates configuration
├── infra/
│   └── terraform/                    # Infrastructure as Code
│       ├── backend.hcl               # Terraform backend configuration
│       ├── providers.tf              # Provider configurations
│       ├── main.tf                   # Main infrastructure resources
│       ├── variables.tf              # Input variables
│       ├── outputs.tf                # Output values
├── src/
│   ├── Dockerfile                    # Container configuration
│   └── app/                          # Application source code
├── CODEOWNERS                        # Code ownership rules
├── LICENSE                           # License file
└── README.md                         # This file
```

## 🚀 Features

-- **Infrastructure as Code**: Complete infrastructure using Terraform
- **CI/CD Pipelines**: Automated testing, building, and deployment
- **Container Ready**: Docker configuration for containerized deployment
- **Monitoring**: Health check endpoints and logging

## 🛠️ Technology Stack

### Application

### Infrastructure

### DevOps
- **CI/CD**: GitHub Actions
- **Container Registry**: GitHub Container Registry
- **Dependency Management**: Dependabot
- **Code Ownership**: CODEOWNERS file

## 🏁 Quick Start

### Prerequisites

- Docker installed
- Terraform installed
- GitHub CLI (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd starter-repo
   ```

2. **Install dependencies**
   ```bash
   cd src/app
   ```

3. **Run the application**
   ```bash
   ```

4. **Run tests**
   ```bash
   ```

5. **Access the application**

### Docker Development

1. **Build the Docker image**
   ```bash
   cd src
   docker build -t webapp-template .
   ```

2. **Run the container**
   ```bash
   docker run -p 3000:3000 webapp-template
   ```

## 🏭 Deployment

### Infrastructure Setup

1. **Configure Terraform backend**
   
   The `infra/terraform/backend.hcl` should pull your Azure container details from env variables.

2. **Initialize and deploy infrastructure**
   ```bash
   cd infra/terraform
   terraform init -backend-config=backend.hcl
   terraform plan
   terraform apply
   ```

### Application Deployment

The application is automatically deployed when code is pushed to the `main` branch. The deployment pipeline:

1. **CI Pipeline** (`ci.yml`): Runs tests and builds the application
2. **Infrastructure Pipeline** (`infra-plan-apply.yml`): Plans and applies infrastructure changes
3. **Deployment Pipeline** (`deploy-webapp.yml`): Builds and deploys the application

### Environment Variables

Configure the following secrets in your GitHub repository by running the script

## 🔧 Configuration

### Terraform Variables

Key variables you can customize in `infra/terraform/variables.tf`:


### Application Configuration

The application can be configured through environment variables:

- `PORT`: Application port (default: 3000)
- `NODE_ENV`: Environment mode (development, production)

## 🧪 Testing

## 📦 Dependencies

### Production Dependencies

### Development Dependencies

## 🤝 Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Ensure tests pass and linting is clean
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

1. Check the [Issues](../../issues) page
2. Review the [Wiki](../../wiki) for additional documentation
3. Contact the maintainers listed in [CODEOWNERS](CODEOWNERS)

---

**Happy coding! 🎉**