# Simple GCP Project Creation via YAML

A comprehensive Infrastructure as Code (IaC) solution for automatically creating Google Cloud Platform (GCP) projects using YAML configuration files. This project combines Terraform, Python automation, and GitHub Actions to provide a streamlined workflow for GCP project provisioning with automated CI/CD capabilities.

## 🎯 Project Overview

This project provides a complete solution for:
- **YAML-based GCP project configuration** - Define projects in simple YAML files
- **Automated Terraform deployment** - Convert YAML to Terraform and deploy infrastructure
- **GitHub Actions CI/CD** - Automated deployment triggered by commits containing "deploy"
- **Slack notifications** - Real-time deployment status updates
- **Infrastructure lifecycle management** - Easy creation and destruction of resources

## 📁 Project Structure

```
Simple-GCP-Project-Creation-via-YAML/
├── .github/
│   └── workflows/
│       └── infrastructure-deploy.yml    # GitHub Actions workflow
├── configs/
│   └── example-project.yaml            # Example project configuration
├── modules/
│   └── project/
│       ├── main.tf                     # Project module Terraform code
│       └── variables.tf                # Project module variables
├── scripts/
│   ├── deploy.py                       # Python deployment script
│   └── destroy.py                      # Python destruction script
├── .gitignore                          # Git ignore rules
├── LICENSE                             # Project license
├── main.tf                             # Root Terraform configuration
├── variables.tf                        # Root Terraform variables
└── README.md                           # This file
```

## 📋 Prerequisites

### Required Software
- **Python 3.7+** - For running deployment scripts
- **Terraform 1.6.0+** - For infrastructure provisioning
- **Google Cloud SDK** - For GCP authentication
- **Git** - For version control

### Required GCP Setup
- **Google Cloud Account** - Active GCP account
- **Billing Account** - Valid billing account with sufficient credits
- **Service Account** (for GitHub Actions) - With appropriate permissions
- **APIs Enabled** - Required GCP APIs must be enabled

### Required Permissions
The service account needs these IAM roles:
- `roles/editor` - For project creation and management
- `roles/billing.user` - For billing account association
- `roles/resourcemanager.projectCreator` - For project creation
- `roles/serviceusage.serviceUsageAdmin` - For API management

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Simple-GCP-Project-Creation-via-YAML.git
cd Simple-GCP-Project-Creation-via-YAML
```

### 2. Install Python Dependencies
```bash
pip install pyyaml
```

### 3. Install Terraform
**Windows:**
```bash
# Using Chocolatey
choco install terraform

# Or download from https://terraform.io/downloads
```

**macOS:**
```bash
# Using Homebrew
brew install terraform
```

**Linux:**
```bash
# Using package manager
sudo apt-get update && sudo apt-get install terraform
```

### 4. Install Google Cloud SDK
**Windows:**
```bash
# Download and install from https://cloud.google.com/sdk/docs/install
```

**macOS:**
```bash
# Using Homebrew
brew install google-cloud-sdk
```

**Linux:**
```bash
# Using package manager
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 5. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud auth application-default login
```

### 6. Set Up GitHub Actions (Optional)
1. Go to your GitHub repository settings
2. Navigate to "Secrets and variables" → "Actions"
3. Add these secrets:
   - `GIT_ACTION_GCP`: Your service account JSON key
   - `SLACK_WEBHOOK_URL`: Your Slack webhook URL (optional)

## 📖 Usage

### Local Deployment

#### 1. Create a Project Configuration
Create a YAML file in the `configs/` directory:

```yaml
# configs/my-project.yaml
project_id: "my-awesome-project-123"
organization_id: "123456789012"  # Optional
billing_account: "01783B-A7A65B-153181"

labels:
  owner: "john-doe"
  environment: "production"
  team: "platform"

apis:
  - compute.googleapis.com
  - iam.googleapis.com
  - storage.googleapis.com
  - bigquery.googleapis.com
```

#### 2. Deploy Infrastructure
```bash
# Deploy using default config
python scripts/deploy.py

# Deploy using specific config
python scripts/deploy.py configs/my-project.yaml
```

#### 3. Destroy Infrastructure
```bash
# Interactive destruction (with confirmation)
python scripts/destroy.py

# Force destruction (no confirmation)
python scripts/destroy.py --force
```

### GitHub Actions Deployment

#### 1. Automatic Deployment
The workflow automatically triggers when:
- A commit message contains the word "deploy"
- Files in the `configs/` directory are modified
- Manual trigger via GitHub Actions UI

#### 2. Trigger Deployment
```bash
# This will trigger deployment
git commit -m "deploy new infrastructure"
git push

# This will NOT trigger deployment
git commit -m "update documentation"
git push
```

#### 3. Manual Deployment
1. Go to GitHub Actions tab
2. Select "Infrastructure Deploy" workflow
3. Click "Run workflow"
4. Specify the YAML file to deploy

## 🔧 Configuration Files Explained

### YAML Configuration (`configs/example-project.yaml`)
```yaml
project_id: "dev-intern-poc"           # Unique GCP project ID
organization_id: null                   # Optional organization ID
billing_account: "01783B-A7A65B-153181" # Required billing account
labels:                                 # Custom labels for organization
  owner: "intern"
  environment: "test"
apis:                                   # GCP APIs to enable
  - compute.googleapis.com
  - iam.googleapis.com
```

### Root Terraform Files

#### `main.tf`
- **Purpose**: Root Terraform configuration
- **Contains**: Provider configuration and module calls
- **Key Features**:
  - Google provider setup
  - Module instantiation
  - Variable passing

#### `variables.tf`
- **Purpose**: Input variable definitions
- **Contains**: All configurable parameters
- **Key Variables**:
  - `project_id`: Target project ID
  - `organization_id`: Organization ID (optional)
  - `billing_account`: Billing account ID
  - `labels`: Project labels
  - `apis`: APIs to enable

### Module Files (`modules/project/`)

#### `main.tf`
- **Purpose**: Core project creation logic
- **Contains**: 
  - `google_project` resource
  - `google_project_service` resources for API enablement
- **Key Features**:
  - Project creation with billing association
  - Automatic API enablement
  - Label management

#### `variables.tf`
- **Purpose**: Module-specific variable definitions
- **Contains**: Input validation and type definitions
- **Key Features**:
  - Type constraints
  - Default values
  - Description documentation

### Python Scripts

#### `scripts/deploy.py`
- **Purpose**: Automated deployment script
- **Features**:
  - YAML to JSON conversion
  - Automatic directory management
  - Terraform execution
  - Error handling
- **Usage**: `python deploy.py [yaml-file]`

#### `scripts/destroy.py`
- **Purpose**: Infrastructure destruction script
- **Features**:
  - Safety confirmations
  - Force mode option
  - Error handling
- **Usage**: `python destroy.py [--force]`

### GitHub Actions Workflow

#### `.github/workflows/infrastructure-deploy.yml`
- **Purpose**: CI/CD automation
- **Triggers**:
  - Push with "deploy" in commit message
  - Manual workflow dispatch
- **Features**:
  - Python environment setup
  - Terraform installation
  - GCP authentication
  - Slack notifications
  - Multi-file processing

## 🛠️ Development Process & Problem Solving

### Initial Setup Challenges

#### Problem 1: Terraform Provider Configuration
**Issue**: `Unexpected attribute: An attribute named "billing_account" is not expected here`
**Root Cause**: `billing_account` and `organization_id` were incorrectly placed in the provider block
**Solution**: Moved these attributes to the module level where they belong

#### Problem 2: PowerShell Command Execution
**Issue**: `&&` operator not recognized in PowerShell
**Root Cause**: PowerShell uses different syntax than bash
**Solution**: Executed commands separately or used PowerShell-specific syntax

#### Problem 3: GCP Authentication
**Issue**: `No credentials loaded` error
**Root Cause**: Missing application default credentials
**Solution**: Ran `gcloud auth application-default login`

#### Problem 4: Google Cloud SDK Installation
**Issue**: `gcloud command not found`
**Root Cause**: SDK not in PATH or not installed
**Solution**: Installed SDK and added to environment variables

### Terraform State Management

#### Problem 5: Project Deletion Policy
**Issue**: `Cannot destroy project as deletion_policy is set to PREVENT`
**Root Cause**: Default deletion policy prevents project destruction
**Solution**: Set `deletion_policy = "DELETE"` for full destruction capability

#### Problem 6: Working Directory Issues
**Issue**: `No configuration files` when running from scripts directory
**Root Cause**: Terraform commands executed from wrong directory
**Solution**: Modified Python scripts to automatically change to project root

### GitHub Actions Challenges

#### Problem 7: Service Account Permissions
**Issue**: Multiple permission errors for billing and project creation
**Root Cause**: Service account lacked necessary IAM roles
**Solution**: Granted required roles:
- `roles/billing.user` on billing account
- `roles/editor` on project
- Enabled required APIs

#### Problem 8: YAML Syntax Errors
**Issue**: Multiple YAML indentation and syntax errors
**Root Cause**: Incorrect nesting and spacing in workflow file
**Solution**: Systematically corrected all indentation issues

#### Problem 9: Conditional Execution
**Issue**: Workflow running on every commit
**Root Cause**: Missing conditional logic
**Solution**: Added `if: contains(github.event.head_commit.message, 'deploy')` condition

### Notification System

#### Problem 10: Slack Integration
**Issue**: Webhook URL not configured
**Root Cause**: Missing secret configuration
**Solution**: Made Slack notifications conditional on secret presence

## 🔍 Troubleshooting

### Common Issues

#### 1. Authentication Errors
```bash
# Error: No credentials loaded
gcloud auth application-default login
```

#### 2. Permission Denied
```bash
# Error: Permission denied on billing account
gcloud alpha billing accounts add-iam-policy-binding BILLING_ACCOUNT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/billing.user"
```

#### 3. API Not Enabled
```bash
# Error: API not enabled
gcloud services enable cloudbilling.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

#### 4. Project ID Already Exists
```bash
# Error: Project ID already exists
# Solution: Use a unique project ID in your YAML file
```

#### 5. Terraform State Issues
```bash
# Error: State file not found
# Solution: Run terraform init first
terraform init
```

### Debug Mode

#### Enable Terraform Debug Logging
```bash
export TF_LOG=DEBUG
python scripts/deploy.py
```

#### Check GitHub Actions Logs
1. Go to Actions tab in GitHub
2. Click on failed workflow run
3. Expand failed step to see detailed logs

## 🚀 Advanced Usage

### Custom API Lists
```yaml
apis:
  - compute.googleapis.com
  - iam.googleapis.com
  - storage.googleapis.com
  - bigquery.googleapis.com
  - cloudfunctions.googleapis.com
  - run.googleapis.com
```

### Environment-Specific Configurations
```yaml
# configs/production.yaml
project_id: "prod-my-app-2024"
labels:
  environment: "production"
  tier: "critical"

# configs/staging.yaml
project_id: "staging-my-app-2024"
labels:
  environment: "staging"
  tier: "development"
```

### Multiple Project Deployment
```bash
# Deploy multiple projects
for config in configs/*.yaml; do
  python scripts/deploy.py "$config"
done
```

## 📊 Monitoring & Notifications

### Slack Integration
- **Success Notifications**: Deployed project details
- **Failure Notifications**: Error details and troubleshooting info
- **Custom Messages**: Include commit info, actor, and file details

### GitHub Actions Status
- **Workflow Status**: Visible in repository Actions tab
- **Step-by-step Logs**: Detailed execution logs
- **Manual Triggers**: On-demand execution capability

## 🔒 Security Considerations

### Service Account Security
- **Principle of Least Privilege**: Only grant necessary permissions
- **Key Rotation**: Regularly rotate service account keys
- **Secret Management**: Store credentials in GitHub Secrets

### Project Isolation
- **Unique Project IDs**: Prevent naming conflicts
- **Label Management**: Use labels for organization and cost tracking
- **Billing Alerts**: Set up billing alerts for cost control

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Standards
- **Python**: Follow PEP 8 guidelines
- **Terraform**: Use consistent formatting
- **YAML**: Maintain proper indentation
- **Documentation**: Update README for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
1. Check the troubleshooting section above
2. Review GitHub Issues for similar problems
3. Create a new issue with detailed error information

### Reporting Bugs
When reporting bugs, please include:
- Error messages (full output)
- Steps to reproduce
- Environment details (OS, Python version, etc.)
- Configuration files (sanitized)

## 🎉 Success Stories

This project has been successfully used to:
- **Automate GCP project provisioning** for development teams
- **Implement Infrastructure as Code** best practices
- **Reduce manual deployment time** from hours to minutes
- **Enable consistent project configurations** across environments
- **Integrate with CI/CD pipelines** for automated deployments

---

**Happy Deploying! 🚀**

For questions or contributions, please open an issue or submit a pull request.
