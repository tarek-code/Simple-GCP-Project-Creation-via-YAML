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
│   ├── example-project.yaml            # Example project configuration
│   └── static-ip-example.yaml          # Static IP examples (VPC, subnets, IPs)
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

#### 1. Commit-based triggers (exact patterns)
On push to `main`, the workflow parses the commit message and only runs when it matches one of these exact patterns (case-insensitive; extra spaces allowed; extra words are not allowed):

- `deploy` → plan only for all changed YAMLs under `configs/`
- `deploy yes` → plan + apply for all changed YAMLs
- `deploy configs/<file>.yaml` → plan only for the specified YAML
- `deploy configs/<file>.yaml yes` → plan + apply for the specified YAML
- `destroy` → plan-only destroy for all changed YAMLs
- `destroy yes` → apply destroy for all changed YAMLs (modules/resources)
- `destroy configs/<file>.yaml` → plan-only destroy for the specified YAML
- `destroy configs/<file>.yaml yes` → apply destroy for the specified YAML

Notes:
- If you include the word `project` in a destroy apply commit (e.g., `destroy configs/<file>.yaml yes project`), the workflow will delete the entire GCP project after destroying modules.
- When no specific file is provided, the workflow targets YAMLs changed in the pushed commit range.
- Any other message results in a quick no-op run.

#### 2. Manual Deployment/Destruction
1. Go to GitHub Actions tab
2. Select "Infrastructure Deploy" workflow
3. Click "Run workflow"
4. Inputs:
   - action: `deploy` or `destroy`
   - files: space-separated YAMLs, e.g. `configs/proj-a.yaml configs/proj-b.yaml`
   - approve: `yes` (apply) or `no` (plan-only)

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

## Supported resource modules (customizable via YAML)

- Project (creation + API enablement)
- VPC, Subnet, Firewall
- Service Account, IAM Binding
- Compute Instance (VM)
- Storage Bucket
- Pub/Sub Topic
- Cloud Run Service
- Cloud SQL Instance
- Artifact Registry Repository
- Secret Manager Secret (+ version)
- Cloud DNS Managed Zone
- BigQuery Dataset
- Cloud Functions (2nd gen)
- GKE (Google Kubernetes Engine) cluster + node pool
- Cloud Router, Cloud NAT
 - Static IP (global/regional)
 - Compute Disk

### YAML schema (excerpt)

Add resources under `resources:` per project YAML:

```yaml
resources:
  vpc:
    name: "vpc-a"
    routing_mode: "GLOBAL"

  subnets:
    - name: "subnet-a1"
      region: "us-central1"
      ip_cidr_range: "10.10.0.0/24"
      network: "vpc-a"

  compute_instances:
    - name: "vm-a1"
      zone: "us-central1-a"
      machine_type: "e2-micro"
      image: "debian-cloud/debian-11"
      subnetwork: "subnet-a1"

  storage_buckets:
    - name: "my-bucket"
      location: "US"
      enable_versioning: true

  pubsub_topics:
    - name: "events"

  cloud_run_services:
    - name: "hello"
      location: "us-central1"
      image: "gcr.io/cloudrun/hello"

  cloud_sql_instances:
    - name: "sql-a"
      database_version: "POSTGRES_14"
      region: "us-central1"
      tier: "db-f1-micro"

  artifact_repos:
    - name: "docker-repo"
      location: "us"
      format: "DOCKER"

  secrets:
    - name: "api-token"
      value: "dummy"

  dns_zones:
    - name: "example-zone"
      dns_name: "example.internal."

  bigquery_datasets:
    - dataset_id: "analytics"
      location: "US"

  cloud_functions:
    - name: "fn-http"
      location: "us-central1"
      runtime: "python311"
      entry_point: "main"
      source_bucket: "code-bucket"
      source_object: "functions/fn-http.zip"

  gke:
    name: "gke-a"
    location: "us-central1"
    node_pool_name: "np-a"
    node_count: 1
    machine_type: "e2-standard-2"

  cloud_router:
    name: "router-a"
    region: "us-central1"
    network: "vpc-a"

  cloud_nat:
    name: "nat-a"
    region: "us-central1"
    router: "router-a"
```

Notes:
- You can declare multiple items for list-based resources (VMs, subnets, buckets, topics, datasets, functions).
- The workflow: `deploy.py` performs plan by default and prompts to apply per project.

## 🧩 Advanced YAML Fields (per module)

The deploy script now supports rich configuration across modules. Below are additional fields you can set under `resources:`.

- Storage Buckets: `force_destroy`, `storage_class`, `public_access_prevention`, `default_kms_key_name`, `logging { log_bucket, log_object_prefix }`, `cors[]`, `lifecycle_rules[]`, `retention_policy { retention_period, is_locked? }`
- Subnets: `secondary_ip_ranges[]` for pod/service secondary ranges
- Firewall: `allows[]`, `denies[]`, `target_service_accounts[]`, `destination_ranges[]`
- Pub/Sub Topics: `subscriptions[]` with `dead_letter_topic`, `filter`, `retry_min_backoff`, `retry_max_backoff`, `push_endpoint`, `oidc_*`
- Cloud SQL: `deletion_protection`, `availability_type`, `disk_size`, `disk_type`, `ipv4_enabled`, `private_network`, `authorized_networks[]`, `backup_configuration`, `maintenance_window`, `database_flags[]`, `insights_config`, `kms_key_name`
- GKE: `network`, `subnetwork`, `cluster_secondary_range_name`, `services_secondary_range_name`, `enable_private_nodes`, `master_ipv4_cidr_block`, `enable_network_policy`, `node_auto_scaling`, `node_labels`, `node_taints`
- Cloud Router: `asn`, `bgp_advertised_ip_ranges[]`, `interfaces[]`, `bgp_peers[]`
- Memorystore Redis: `maintenance_policy`, `persistence_config`
- Secret Manager: `replication` (auto or user-managed with CMEK), `additional_versions[]`
- Cloud DNS Zones: `record_sets[]`
- IAM Bindings: `members[]` and optional `condition { title, expression, description? }`

See examples throughout the YAML User Manual section above for concrete snippets using these fields.

## 📈 Coverage

- Feature coverage (for supported services): ~80% of commonly used options; ~60–70% if you consider the entire GCP feature surface across all services.
- Module coverage (how many GCP products we have modules for): ~30–40% of GCP services (core infra and app platforms). Not yet covered are many data/ML and specialized services (e.g., Vertex AI, Dataflow/Dataproc, advanced BigQuery features, Dataplex, Pub/Sub Lite, advanced KMS/SCC/org policies, full load balancing/PSC/VPN/Interconnect, etc.).

## 🧪 GitHub Actions usage (quick guide)

- Commit-triggered:
  - Plan only on changed YAMLs under `configs/`: commit message contains `deploy`
  - Apply automatically: commit message contains `deploy yes`
  - Destroy modules: commit message contains `destroy yes`
  - Destroy entire project: commit message contains `destroy yes project`
  - Note: The workflow picks YAML files from the commit diff (files changed in `configs/`). If a file didn’t change, use manual dispatch.

- Manual dispatch (Actions → Infrastructure Deploy/Destroy → Run workflow):
  - `action`: `deploy` or `destroy`
  - `files`: space-separated YAMLs, e.g. `configs/proj-a.yaml configs/proj-b.yaml`
  - `approve`: `yes` (apply) or `no` (plan-only)


## 📚 YAML User Manual

This section explains exactly how to write YAML files in `configs/` to compose infrastructure using the available modules. Each YAML file represents one GCP project.

### 1) Top-level required fields

```yaml
project_id: "my-project-id"         # required, must be globally unique
billing_account: "AAAAAA-BBBBBB-CCCCCC"  # required unless project already exists and is billed
organization_id: "123456789012"     # optional, set if creating under an org/folder
labels:                              # optional
  key: value
apis:                                # strongly recommended; enable what you need
  - compute.googleapis.com
  - iam.googleapis.com
  - storage.googleapis.com
  - run.googleapis.com
resources: {}                        # optional; define modules here
```

Tips:
- If the project already exists, the system will detect it and skip creation but will still enable `apis`.
- Use short, DNS-safe names (letters, numbers, hyphens) for resources that become GCP names.

### 2) Referencing between resources

- Many modules accept names that refer to other declared resources in the same YAML.
- Common references:
  - Subnet `network` must match the VPC `name`.
  - VM `subnetwork` must match a declared subnet `name`.
  - Cloud Run `vpc_connector` must match a declared Serverless VPC Connector `name`.
  - Cloud NAT `router` must match a declared Cloud Router `name`.

The deployer wires safe `depends_on` automatically when it detects these references.

### 3) Module blocks under `resources:`

Add only what you need. Omit anything you are not using. List-based modules accept multiple entries.

#### VPC
```yaml
resources:
  vpc:
    name: vpc-a
    routing_mode: GLOBAL           # GLOBAL or REGIONAL (default GLOBAL)
    description: "Shared VPC"
```

#### Subnets (list)
```yaml
resources:
  subnets:
    - name: subnet-a1
      region: us-central1
      ip_cidr_range: 10.10.0.0/24
      network: vpc-a
      private_ip_google_access: true       # optional
```

#### Firewall rules (list)
```yaml
resources:
  firewall_rules:
    - name: allow-ssh
      network: vpc-a
      direction: INGRESS                  # optional (INGRESS default)
      priority: 1000                      # optional
      ranges: ["0.0.0.0/0"]
      allow:
        - protocol: tcp
          ports: ["22"]
```

#### Service accounts (list)
```yaml
resources:
  service_accounts:
    # Basic service account
    - account_id: "vm-runtime"
      display_name: "VM Runtime Service Account"
      description: "Service account for VM operations"
    
    # Application service account
    - account_id: "app-service"
      display_name: "Application Service Account"
      description: "Service account for application services"
    
    # Database service account
    - account_id: "db-service"
      display_name: "Database Service Account"
      description: "Service account for database operations"
    
    # CI/CD service account
    - account_id: "cicd-pipeline"
      display_name: "CI/CD Pipeline Service Account"
      description: "Service account for CI/CD operations"
    
    # Monitoring service account
    - account_id: "monitoring-agent"
      display_name: "Monitoring Agent Service Account"
      description: "Service account for monitoring and logging"
```

**Service Account Features:**
- **Account ID**: Unique identifier (no domain suffix)
- **Display Name**: Human-readable name
- **Description**: Purpose and usage description
- **IAM Integration**: Use with `iam_bindings` for role assignment
- **Cross-Service**: Can be used across multiple GCP services

#### IAM bindings (list)
```yaml
resources:
  iam_bindings:
    - role: roles/storage.admin
      member: serviceAccount:vm-runtime@my-project-id.iam.gserviceaccount.com
```

#### Compute instances (VMs) (list)
```yaml
resources:
  compute_instances:
    - name: vm-a1
      zone: us-central1-a
      machine_type: e2-micro
      image: debian-cloud/debian-11
      subnetwork: subnet-a1
      tags: ["ssh"]                      # optional
      metadata: { startup-script: "#!/bin/bash\necho hi" }  # optional
```

#### Storage buckets (list)
```yaml
resources:
  storage_buckets:
    - name: my-bucket
      location: US
      enable_versioning: true
      uniform_bucket_level_access: true
      labels: { purpose: backups }
```

#### Pub/Sub topics (list)
```yaml
resources:
  pubsub_topics:
    # Simple topic
    - name: "events"
      labels: { env: "dev", purpose: "events" }
    
    # Topic with subscriptions
    - name: "user-notifications"
      labels: { env: "prod", service: "notifications" }
      subscriptions:
        - name: "email-subscription"
          ack_deadline_seconds: 60
          retain_acked_messages: true
          message_retention_duration: "604800s"  # 7 days
        
        - name: "push-subscription"
          push_endpoint: "https://my-app.com/webhook"
          oidc_service_account_email: "notifications@my-project.iam.gserviceaccount.com"
          oidc_audience: "my-app-audience"
          retry_min_backoff: "10s"
          retry_max_backoff: "600s"
        
        - name: "dead-letter-subscription"
          dead_letter_topic: "failed-notifications"
          max_delivery_attempts: 5
          filter: "attributes.status=\"failed\""
          expiration_policy_ttl: "86400s"  # 24 hours
```

**Pub/Sub Features:**
- **Topics**: Message publishing endpoints
- **Subscriptions**: Message consumption endpoints
- **Push/Pull**: Push to webhooks or pull by consumers
- **Dead Letter**: Failed message handling
- **Retry Policies**: Custom retry backoff
- **Message Filtering**: Attribute-based filtering
- **Retention**: Message retention policies

#### Serverless VPC Connectors (list)
Prerequisites: VPC must exist in the same project. Choose a dedicated CIDR that does not overlap subnets.
```yaml
resources:
  serverless_vpc_connectors:
    - name: run-connector
      region: us-central1
      network: vpc-a
      ip_cidr_range: 10.8.0.0/28
```

#### Cloud Run services (list)
```yaml
resources:
  cloud_run_services:
    - name: hello
      location: us-central1
      image: nginxinc/nginx-unprivileged:stable-alpine
      allow_unauthenticated: true           # optional
      vpc_connector: run-connector          # optional
      egress: all-traffic                   # one of: all, all-traffic, private-ranges-only
```

#### Cloud SQL instances (list)
```yaml
resources:
  cloud_sql_instances:
    - name: sql-a
      database_version: POSTGRES_14
      region: us-central1
      tier: db-f1-micro
```

#### Artifact Registry (list)
```yaml
resources:
  artifact_repos:
    - name: docker-repo
      location: us
      format: DOCKER
```

#### Secret Manager (list)
```yaml
resources:
  secrets:
    - name: api-token
      value: "dummy"
```

#### Cloud DNS managed zones (list)
```yaml
resources:
  dns_zones:
    # Public DNS zone
    - name: "my-domain-zone"
      dns_name: "example.com."
      description: "Public DNS zone for example.com"
      record_sets:
        - name: "example.com."
          type: "A"
          ttl: 300
          rrdatas: ["1.2.3.4"]
        
        - name: "www.example.com."
          type: "CNAME"
          ttl: 300
          rrdatas: ["example.com."]
        
        - name: "api.example.com."
          type: "A"
          ttl: 300
          rrdatas: ["5.6.7.8"]
        
        - name: "example.com."
          type: "MX"
          ttl: 300
          rrdatas: ["10 mail.example.com."]
        
        - name: "example.com."
          type: "TXT"
          ttl: 300
          rrdatas: ["\"v=spf1 include:_spf.google.com ~all\""]
    
    # Private DNS zone
    - name: "internal-zone"
      dns_name: "internal.company."
      description: "Private DNS zone for internal services"
      record_sets:
        - name: "db.internal.company."
          type: "A"
          ttl: 300
          rrdatas: ["10.0.1.100"]
        
        - name: "api.internal.company."
          type: "A"
          ttl: 300
          rrdatas: ["10.0.1.200"]
        
        - name: "cache.internal.company."
          type: "CNAME"
          ttl: 300
          rrdatas: ["redis.internal.company."]
```

**DNS Record Types:**
- **A**: IPv4 address records
- **AAAA**: IPv6 address records  
- **CNAME**: Canonical name (alias)
- **MX**: Mail exchange records
- **TXT**: Text records (SPF, DKIM, etc.)
- **NS**: Name server records
- **SRV**: Service records

#### BigQuery datasets (list)
```yaml
resources:
  bigquery_datasets:
    - dataset_id: analytics
      location: US
```

#### Static IPs (list)
```yaml
resources:
  static_ips:
    # External Regional Static IP
    - name: "web-server-external-ip"
      address_type: "EXTERNAL"          # EXTERNAL (default) or INTERNAL
      region: "us-central1"             # required for regional IPs
      description: "External static IP for web server"
      network_tier: "PREMIUM"           # PREMIUM or STANDARD (for external)
    
    # External Global Static IP (no region specified)
    - name: "global-lb-ip"
      address_type: "EXTERNAL"
      description: "Global static IP for load balancer"
      network_tier: "PREMIUM"
    
    # Internal Regional Static IP
    - name: "internal-api-ip"
      address_type: "INTERNAL"
      region: "us-central1"
      subnetwork: "demo-subnet"         # required for INTERNAL addresses
      purpose: "GCE_ENDPOINT"           # GCE_ENDPOINT, VPC_PEERING, etc.
      description: "Internal static IP for API server"
    
    # Internal IP with specific address
    - name: "database-internal-ip"
      address_type: "INTERNAL"
      region: "us-central1"
      subnetwork: "demo-subnet"
      address: "10.0.0.100"            # optional specific IP, or auto-allocate
      purpose: "GCE_ENDPOINT"
      description: "Internal static IP for database (fixed address)"
```

**Static IP Types:**
- **EXTERNAL**: Public IPs accessible from internet (no VPC required)
- **INTERNAL**: Private IPs within VPC (requires subnetwork)

**Key Fields:**
- `region`: Required for regional IPs, omit for global IPs
- `subnetwork`: Required for INTERNAL IPs (must reference existing subnet)
- `purpose`: For INTERNAL IPs (GCE_ENDPOINT, VPC_PEERING, etc.)
- `address`: Optional specific IP to assign, or let Google auto-allocate
- `network_tier`: PREMIUM or STANDARD (for external IPs)

#### Compute disks (list)
```yaml
resources:
  disks:
    # Standard persistent disk
    - name: "data-disk-a"
      zone: "us-central1-a"
      size_gb: 100
      type: "pd-standard"                # pd-standard, pd-ssd, pd-balanced
      labels: { role: "data", env: "prod" }
    
    # SSD persistent disk
    - name: "cache-disk-b"
      zone: "us-central1-a"
      size_gb: 50
      type: "pd-ssd"
      labels: { role: "cache", env: "prod" }
    
    # Balanced persistent disk
    - name: "app-disk-c"
      zone: "us-central1-a"
      size_gb: 200
      type: "pd-balanced"
      labels: { role: "application", env: "prod" }
    
    # Disk from image
    - name: "boot-disk-d"
      zone: "us-central1-a"
      size_gb: 20
      type: "pd-ssd"
      image: "projects/debian-cloud/global/images/family/debian-11"
      labels: { role: "boot", env: "dev" }
    
    # Disk from snapshot
    - name: "restored-disk-e"
      zone: "us-central1-a"
      size_gb: 150
      type: "pd-standard"
      snapshot: "my-backup-snapshot"
      labels: { role: "restored", env: "dev" }
    
    # Encrypted disk
    - name: "secure-disk-f"
      zone: "us-central1-a"
      size_gb: 100
      type: "pd-ssd"
      kms_key_self_link: "projects/my-project/locations/us-central1/keyRings/my-ring/cryptoKeys/my-key"
      labels: { role: "secure", env: "prod" }
```

**Disk Types:**
- **pd-standard**: Standard persistent disk (HDD)
- **pd-ssd**: SSD persistent disk (high performance)
- **pd-balanced**: Balanced persistent disk (cost-effective SSD)

**Key Features:**
- **Size**: Configurable disk size in GB
- **Zone**: Must match VM zone for attachment
- **Image**: Create disk from existing image
- **Snapshot**: Restore disk from snapshot
- **Encryption**: Customer-managed encryption keys (CMEK)
- **Labels**: Custom metadata for organization

#### Cloud Functions (2nd gen) (list)
```yaml
resources:
  cloud_functions:
    - name: fn-http
      location: us-central1
      runtime: python311
      entry_point: main
      source_bucket: code-bucket
      source_object: functions/fn-http.zip
```

#### GKE cluster (single object)
```yaml
resources:
  gke:
    name: gke-a
    location: us-central1
    node_pool_name: np-a
    node_count: 1
    machine_type: e2-standard-2
```

#### Cloud Router (single object)
```yaml
resources:
  cloud_router:
    name: router-a
    region: us-central1
    network: vpc-a
```

#### Cloud NAT (single object)
```yaml
resources:
  cloud_nat:
    name: nat-a
    region: us-central1
    router: router-a
```

#### Memorystore Redis (list)
```yaml
resources:
  memorystore_redis:
    - name: redis-a
      region: us-central1
      tier: BASIC
      memory_size_gb: 1
```

### 4) API checklist per feature

Enable the APIs you need in the top-level `apis:` list. Common examples:
- VMs, VPC: `compute.googleapis.com`
- Cloud Run: `run.googleapis.com`, VPC connector: `vpcaccess.googleapis.com`
- Cloud SQL: `sqladmin.googleapis.com`
- Artifact Registry: `artifactregistry.googleapis.com`
- Secret Manager: `secretmanager.googleapis.com`
- GKE: `container.googleapis.com`
- BigQuery: `bigquery.googleapis.com`
- Cloud Functions: `cloudfunctions.googleapis.com`, plus source storage API if pulling from bucket

### 5) End-to-end examples

Minimal Cloud Run + VPC connector + VPC/Subnet:
```yaml
project_id: dev-intern-poc
billing_account: "01783B-A7A65B-153181"
apis:
  - run.googleapis.com
  - compute.googleapis.com
  - vpcaccess.googleapis.com
resources:
  vpc:
    name: vpc-run
  subnets:
    - name: subnet-run
      region: us-central1
      ip_cidr_range: 10.20.0.0/24
      network: vpc-run
  serverless_vpc_connectors:
    - name: run-connector
      region: us-central1
      network: vpc-run
      ip_cidr_range: 10.8.0.0/28
  cloud_run_services:
    - name: hello-run
      location: us-central1
      image: nginxinc/nginx-unprivileged:stable-alpine
      allow_unauthenticated: true
      vpc_connector: run-connector
      egress: all-traffic
```

### 6) Running

```bash
python scripts/deploy.py configs/my-project.yaml
```

The script runs `terraform plan` by default and asks for confirmation before applying changes per project.

