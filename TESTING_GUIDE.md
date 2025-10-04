# Comprehensive Testing Guide

This guide covers testing all 22 modules and every scenario in the GCP project creation system.

## 🎯 Test Configuration Files

### 1. `configs/comprehensive-test.yaml`
**Purpose**: Tests ALL 22 modules with advanced configurations
**Resources**: 50+ resources across all categories
**Use Case**: Full system validation

### 2. `configs/test-destroy-scenarios.yaml`
**Purpose**: Minimal config for testing destroy scenarios
**Resources**: 5 basic resources
**Use Case**: Destroy pattern validation

## 📋 Testing Scenarios

### Phase 1: Comprehensive Module Testing

#### Test All 22 Modules
```bash
# Deploy comprehensive test (plan only)
git commit -m "deploy configs/comprehensive-test.yaml"

# Deploy comprehensive test (auto-apply)
git commit -m "deploy configs/comprehensive-test.yaml yes"
```

**Modules Tested:**
- ✅ **VPC Networking** (6 modules)
  - VPC with custom routing
  - Multiple subnets with secondary ranges
  - Firewall rules (ingress/egress)
  - Static IPs (external/internal/global)
  - Cloud Router with BGP
  - Cloud NAT with auto-allocation

- ✅ **Compute Resources** (3 modules)
  - Compute instances (multiple zones)
  - Disks (standard/SSD/balanced)
  - GKE cluster with private nodes

- ✅ **Serverless** (3 modules)
  - Serverless VPC connector
  - Cloud Run services (with VPC)
  - Cloud Functions (HTTP + Pub/Sub)

- ✅ **Storage & Databases** (4 modules)
  - Storage buckets (with lifecycle)
  - Cloud SQL (PostgreSQL + MySQL)
  - BigQuery datasets
  - Memorystore Redis (Basic + HA)

- ✅ **Security & IAM** (3 modules)
  - Service accounts (multiple)
  - IAM bindings (with conditions)
  - Secret Manager (with versions)

- ✅ **Messaging & DNS** (3 modules)
  - Pub/Sub topics (with subscriptions)
  - Cloud DNS zones (public + private)
  - Artifact Registry (Docker + Maven)

### Phase 2: Destroy Scenario Testing

#### Test All Destroy Patterns

**1. Module-Level Destruction (m)**
```bash
# Plan only
git commit -m "destroy configs/test-destroy-scenarios.yaml"

# Auto-apply (module-level)
git commit -m "destroy configs/test-destroy-scenarios.yaml yes"
```

**2. Project-Level Destruction (p)**
```bash
# Auto-apply (project-level)
git commit -m "destroy configs/test-destroy-scenarios.yaml yes project cleanup"
```

**3. All Files Destruction**
```bash
# Module-level for all files
git commit -m "destroy yes"

# Project-level for all files
git commit -m "destroy yes project cleanup"
```

**4. Manual Workflow Dispatch**
- Go to GitHub Actions → Infrastructure Deploy/Destroy
- Test all input combinations:
  - action: `deploy` / `destroy`
  - files: specific files / empty
  - approve: `yes` / `no`

### Phase 3: Edge Case Testing

#### Test Error Scenarios
```bash
# Invalid commit messages (should skip)
git commit -m "random message"
git commit -m "deploy invalid-file.yaml"
git commit -m "destroy without yes"

# Missing files (should skip)
git commit -m "deploy configs/nonexistent.yaml"
```

#### Test Resource Dependencies
- VPC → Subnets → VMs
- Service Accounts → IAM Bindings
- VPC Connector → Cloud Run
- Pub/Sub Topics → Cloud Functions

## 🔍 Validation Checklist

### Deployment Validation
- [ ] All 22 modules deploy successfully
- [ ] Resource dependencies are created in correct order
- [ ] All APIs are enabled automatically
- [ ] Labels and metadata are applied correctly
- [ ] VPC networking works (private IPs, NAT, etc.)
- [ ] GKE cluster is accessible
- [ ] Cloud Run services respond
- [ ] Cloud Functions trigger correctly
- [ ] Storage buckets are accessible
- [ ] Cloud SQL instances are running
- [ ] BigQuery datasets are queryable
- [ ] Redis instances are accessible
- [ ] Pub/Sub messages flow correctly
- [ ] DNS records resolve
- [ ] Artifact Registry accepts pushes
- [ ] Service accounts have correct permissions
- [ ] Secrets are accessible
- [ ] IAM bindings work as expected

### Destroy Validation
- [ ] Plan-only mode shows correct destruction preview
- [ ] Module-level destruction (m) removes resources but keeps project
- [ ] Project-level destruction (p) removes entire project
- [ ] Commit message patterns work correctly
- [ ] Manual workflow dispatch works
- [ ] Slack notifications are sent
- [ ] Terraform state is persisted
- [ ] Error handling works for invalid inputs

### GitHub Actions Validation
- [ ] Workflow triggers on correct commit messages
- [ ] Workflow skips on invalid messages
- [ ] Manual dispatch works with all inputs
- [ ] Python environment setup works
- [ ] Terraform installation works
- [ ] GCP authentication works
- [ ] File parsing works correctly
- [ ] Multi-file processing works
- [ ] State persistence works
- [ ] Slack notifications work
- [ ] Error handling and notifications work

## 🚨 Real Issues Encountered & Solutions

### Configuration Errors (Fixed During Testing)

#### 1. **Secret Manager Replication Format Error**
**Error**: `Invalid value for input variable: object required, but have string`
```yaml
# ❌ WRONG
replication: "automatic"
replication: "user_managed"

# ✅ CORRECT
replication:
  auto: true
replication:
  user_managed:
    - location: "us-central1"
    - location: "us-west1"
```

#### 2. **Secret Manager Additional Versions Format Error**
**Error**: `element 0: string required, but have object`
```yaml
# ❌ WRONG
additional_versions:
  - value: "old-secret"
    enabled: false

# ✅ CORRECT
additional_versions:
  - "old-secret"
```

#### 3. **Cloud SQL Encryption Key Name Error**
**Error**: `Unsupported block type: encryption_key_name`
**Fix**: Changed from dynamic block to direct attribute in `modules/cloud_sql/main.tf`
```hcl
# ❌ WRONG
dynamic "encryption_key_name" {
  for_each = var.kms_key_name == null ? [] : [1]
  content  = var.kms_key_name
}

# ✅ CORRECT
encryption_key_name = var.kms_key_name
```

#### 4. **Project ID Shell Command Error**
**Error**: `$(date +%s)` not expanded in YAML
```yaml
# ❌ WRONG
project_id: "comprehensive-test-$(date +%s)"

# ✅ CORRECT
project_id: "comprehensive-test-20250103"
```

#### 5. **Cloud Router BGP Configuration Error**
**Error**: `advertised_ip_ranges cannot be specified when using advertise_mode DEFAULT`
**Fix**: Removed `bgp_advertised_ip_ranges` from Cloud Router configuration
```yaml
# ❌ WRONG
cloud_router:
  name: "test-router"
  asn: 65001
  bgp_advertised_ip_ranges:
    - range: "10.10.0.0/24"

# ✅ CORRECT
cloud_router:
  name: "test-router"
  asn: 65001
```

#### 6. **Network Reference Format Errors**
**Error**: `doesn't match regexp` for private_network and authorized_network
**Fix**: Use full self-links instead of names
```yaml
# ❌ WRONG
private_network: "test-vpc"
authorized_network: "test-vpc"

# ✅ CORRECT
private_network: "projects/comprehensive-test-20250103/global/networks/test-vpc"
authorized_network: "projects/comprehensive-test-20250103/global/networks/test-vpc"
```

#### 7. **Firewall Rules Configuration Conflict**
**Error**: `target_tags conflicts with target_service_accounts`
**Fix**: Modified firewall module to handle both conditions
```hcl
# In modules/firewall/main.tf
target_tags             = length(var.target_tags) > 0 ? var.target_tags : null
target_service_accounts = length(var.target_service_accounts) > 0 ? var.target_service_accounts : null
```

#### 8. **Firewall Rules Field Names Error**
**Error**: Wrong field names in YAML configuration
```yaml
# ❌ WRONG
ranges: ["0.0.0.0/0"]
allow:
  - protocol: "tcp"

# ✅ CORRECT
source_ranges: ["0.0.0.0/0"]
allows:
  - protocol: "tcp"
```

#### 9. **Secret Manager Replication Logic Error**
**Error**: `argument must not be null` in replication logic
**Fix**: Fixed null handling in `modules/secret_manager/main.tf`
```hcl
# ❌ WRONG
for_each = var.replication == null || try(var.replication.auto, true) ? [1] : []

# ✅ CORRECT
for_each = var.replication == null || try(var.replication.auto, false) == true ? [1] : []
```

#### 10. **Subnet Secondary IP Ranges Error**
**Error**: `each.value cannot be used in this context`
**Fix**: Changed `each.value` to `secondary_ip_range.value` in subnet module
```hcl
# ❌ WRONG
range_name    = each.value.range_name
ip_cidr_range = each.value.ip_cidr_range

# ✅ CORRECT
range_name    = secondary_ip_range.value.range_name
ip_cidr_range = secondary_ip_range.value.ip_cidr_range
```

#### 11. **Secret Manager Customer Managed Encryption Error**
**Error**: `Missing required argument: kms_key_name`
**Fix**: Made customer_managed_encryption conditional
```hcl
# ❌ WRONG
customer_managed_encryption {
  kms_key_name = try(replicas.value.kms_key_name, null)
}

# ✅ CORRECT
dynamic "customer_managed_encryption" {
  for_each = try(replicas.value.kms_key_name, null) != null ? [1] : []
  content {
    kms_key_name = replicas.value.kms_key_name
  }
}
```

### Common Issues
1. **API Quotas**: Some APIs have daily quotas
   - **Solution**: Use different regions/zones
   - **Solution**: Stagger deployments

2. **Resource Limits**: GCP has per-project limits
   - **Solution**: Use minimal configurations for testing
   - **Solution**: Clean up after testing

3. **Billing**: Comprehensive test uses many resources
   - **Solution**: Use minimal configs for regular testing
   - **Solution**: Set up billing alerts

4. **Timeouts**: Large deployments may timeout
   - **Solution**: Break into smaller chunks
   - **Solution**: Use faster machine types

### Debugging Commands
```bash
# Check deployment status
gcloud projects list --filter="name:comprehensive-test"

# Check resource status
gcloud compute instances list --project=comprehensive-test-*

# Check logs
gcloud logging read "resource.type=gce_instance" --project=comprehensive-test-*

# Check billing
gcloud billing accounts list
gcloud billing projects list --billing-account=01783B-A7A65B-153181
```

## 🎓 Lessons Learned

### Key Takeaways from Real Testing

1. **YAML Configuration Validation**: Always validate YAML syntax and field names against module variables
2. **Terraform Module Dependencies**: Understand how modules reference each other (network names vs self-links)
3. **GCP Resource Requirements**: Some resources require specific formats (full self-links, not just names)
4. **Dynamic Block Logic**: Be careful with `for_each` and `each.value` usage in Terraform
5. **Null Handling**: Properly handle null values in conditional logic
6. **Resource Conflicts**: Some GCP resources have mutually exclusive attributes
7. **Shell Command Limitations**: YAML doesn't expand shell commands like `$(date +%s)`

### Best Practices Discovered

1. **Use Full Self-Links**: Always use complete GCP resource self-links for references
2. **Validate Module Variables**: Check `variables.tf` files to understand expected input formats
3. **Test Incrementally**: Start with minimal configurations and add complexity gradually
4. **Handle Edge Cases**: Consider null values, empty lists, and optional parameters
5. **Document Fixes**: Keep track of configuration errors and their solutions
6. **Use Conditional Logic**: Make optional attributes truly optional with proper null handling

## 📊 Test Results Tracking

### Success Criteria
- ✅ All 22 modules deploy without errors
- ✅ All destroy scenarios work correctly
- ✅ GitHub Actions workflow handles all patterns
- ✅ Resource dependencies are respected
- ✅ Error handling works as expected
- ✅ Notifications are sent correctly
- ✅ State persistence works
- ✅ Performance is acceptable (< 30 minutes for full deployment)

### Test Report Template
```
Test Date: [DATE]
Tester: [NAME]
Environment: [ENVIRONMENT]

Module Tests:
- VPC Networking: ✅/❌
- Compute Resources: ✅/❌
- Serverless: ✅/❌
- Storage & Databases: ✅/❌
- Security & IAM: ✅/❌
- Messaging & DNS: ✅/❌

Destroy Tests:
- Module-level (m): ✅/❌
- Project-level (p): ✅/❌
- Plan-only: ✅/❌
- Manual dispatch: ✅/❌

Issues Found:
- [ISSUE 1]
- [ISSUE 2]

Recommendations:
- [RECOMMENDATION 1]
- [RECOMMENDATION 2]
```

## 🎯 Next Steps

1. **Run Comprehensive Test**: Deploy `comprehensive-test.yaml`
2. **Validate All Modules**: Check each resource type
3. **Test Destroy Scenarios**: Test all destroy patterns
4. **Document Issues**: Record any problems found
5. **Optimize Configurations**: Improve based on results
6. **Create Test Automation**: Automate regular testing

---

**Happy Testing! 🚀**

Remember to clean up test resources after validation to avoid unnecessary costs.
