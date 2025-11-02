# Comprehensive Resource Generation Test

## Test Purpose
Verify that ALL resources appear correctly in generated Terraform and YAML files, including testing multiple instances of the same resource type.

## Test Matrix

### Single Instance Tests

| Resource | Test Action | Expected Result | YAML | Terraform |
|----------|-------------|-----------------|------|-----------|
| VPC Network | Create 1 VPC | 1 `google_compute_network` | ✅ | ✅ |
| Subnet | Create 1 subnet | 1 `google_compute_subnetwork` | ✅ | ✅ |
| Firewall Rule | Create 1 rule | 1 `google_compute_firewall` | ✅ | ✅ |
| Service Account | Create 1 SA | 1 `google_service_account` + roles | ✅ | ✅ |
| IAM Policy | Create 1 policy | 1 `google_project_iam_member` | ✅ | ✅ |
| **Compute Instance** | **Create 1 VM** | **1 `google_compute_instance`** | ✅ | ✅ |
| Storage Bucket | Create 1 bucket | 1 `google_storage_bucket` | ✅ | ✅ |
| Pub/Sub Topic | Create 1 topic | 1 `google_pubsub_topic` | ✅ | ✅ |
| Cloud Run | Create 1 service | 1 `google_cloud_run_service` | ✅ | ✅ |
| Cloud SQL | Create 1 instance | 1 `google_sql_database_instance` | ✅ | ✅ |
| Artifact Registry | Create 1 repo | 1 `google_artifact_registry_repository` | ✅ | ✅ |
| Secret Manager | Create 1 secret | 1 `google_secret_manager_secret` | ✅ | ✅ |
| DNS Zone | Create 1 zone | 1 `google_dns_managed_zone` | ✅ | ✅ |
| BigQuery Dataset | Create 1 dataset | 1 `google_bigquery_dataset` | ✅ | ✅ |
| Cloud Function | Create 1 function | 1 `google_cloudfunctions_function` | ✅ | ✅ |
| Static IP | Create 1 IP | 1 `google_compute_address` | ✅ | ✅ |
| Persistent Disk | Create 1 disk | 1 `google_compute_disk` | ✅ | ✅ |
| Redis Instance | Create 1 redis | 1 `google_redis_instance` | ✅ | ✅ |
| VPC Connector | Create 1 connector | 1 `google_vpc_access_connector` | ✅ | ✅ |
| GKE Cluster | Create 1 cluster | 1 `google_container_cluster` | ✅ | ✅ |
| Cloud Router | Create 1 router | 1 `google_compute_router` | ✅ | ✅ |
| Cloud NAT | Create 1 NAT | 1 `google_compute_router_nat` | ✅ | ✅ |

### Multiple Instance Tests (CRITICAL)

| Resource | Test Action | Expected Result | Status |
|----------|-------------|-----------------|--------|
| **Compute Instances** | **Create 2 VMs with different names** | **2 `google_compute_instance` resources** | **TEST THIS** |
| Storage Buckets | Create 2 buckets | 2 `google_storage_bucket` resources | ✅ |
| Firewall Rules | Create 2 rules | 2 `google_compute_firewall` resources | ✅ |
| Service Accounts | Create 2 SAs | 2 `google_service_account` resources | ✅ |
| Subnets | Create 2 subnets | 2 `google_compute_subnetwork` resources | ✅ |
| Static IPs | Create 2 IPs | 2 `google_compute_address` resources | ✅ |
| Pub/Sub Topics | Create 2 topics | 2 `google_pubsub_topic` resources | ✅ |

## Specific Test for Compute Instances (User's Issue)

### Setup
1. Start app: `streamlit run gui/streamlit_app.py`
2. Fill in Project ID: `test-multi-vm`
3. Check "💻 Create Compute Instances"

### Test Case 1: Create First Instance
1. Fill in:
   - Name: `vm-instance-1`
   - Zone: `us-central1-a`
   - Machine Type: `e2-standard-2`
2. Click "➕ Add"
3. Verify: Instance appears in the list above

### Test Case 2: Create Second Instance
1. Fill in NEW form (should still be visible):
   - Name: `vm-instance-2`
   - Zone: `us-central1-b`
   - Machine Type: `e2-standard-4`
2. Click "➕ Add"
3. Verify: BOTH instances appear in the list

### Test Case 3: Generate Files
1. Click "Generate Terraform Files"
2. **EXPECTED in main.tf:**
```hcl
resource "google_compute_instance" "vm_1" {
  name         = "vm-instance-1"
  zone         = "us-central1-a"
  machine_type = "e2-standard-2"
  # ... full configuration
}

resource "google_compute_instance" "vm_2" {
  name         = "vm-instance-2"
  zone         = "us-central1-b"
  machine_type = "e2-standard-4"
  # ... full configuration
}
```

3. **VERIFY:**
   - [ ] Two separate `resource "google_compute_instance"` blocks
   - [ ] `vm_1` with name "vm-instance-1"
   - [ ] `vm_2` with name "vm-instance-2"
   - [ ] Both have complete configuration

### Test Case 4: YAML Generation
1. Click "Generate YAML Configuration"
2. **EXPECTED in YAML:**
```yaml
resources:
  compute_instances:
    - name: vm-instance-1
      zone: us-central1-a
      machine_type: e2-standard-2
      # ... full config
    - name: vm-instance-2
      zone: us-central1-b
      machine_type: e2-standard-4
      # ... full config
```

3. **VERIFY:**
   - [ ] Two items in `compute_instances` list
   - [ ] Both instances present with all fields

## Debug Steps if Compute Instances Fail

### Check Session State
The data flow should be:
1. User fills form
2. Clicks "➕ Add"
3. Code at line 3768: `st.session_state.compute_instances.append(new_vm)`
4. Page reruns
5. Line 3772: `resources["compute_instances"] = st.session_state.compute_instances`
6. Generation pulls from resources_from_state (line 4443, 4561)
7. Generation loops through all instances (line 262)

### Potential Issues
1. **Same Name**: If both VMs have same name, might cause issues
   - **Fix**: Use unique names
2. **Not in session_state**: Fixed in our update
3. **Generation loop issue**: Should work (uses enumerate)
4. **Resource not in resources_from_state**: Fixed - it's at lines 4443, 4561

### Verification Code Path

```python
# Configuration (line 3768)
st.session_state.compute_instances.append(new_vm)

# Add to local resources (line 3772)
if st.session_state.compute_instances:
    resources["compute_instances"] = st.session_state.compute_instances

# YAML Generation (line 4443)
if st.session_state.get("compute_instances"):
    resources_from_state["compute_instances"] = st.session_state.compute_instances

# Terraform Generation (line 4561)
if st.session_state.get("compute_instances"):
    resources_from_state["compute_instances"] = st.session_state.compute_instances

# Terraform Resource Generation (line 262)
for i, vm in enumerate(resources.get("compute_instances", []), 1):
    # Generates google_compute_instance.vm_{i}
```

## Expected Behavior

### When Code is Working Correctly:
1. ✅ Each "➕ Add" creates a new entry in session_state list
2. ✅ All entries persist even if checkbox unchecked
3. ✅ YAML shows all instances in a list
4. ✅ Terraform creates separate resources (vm_1, vm_2, vm_3, etc.)
5. ✅ Each resource has unique name based on enumerate index

### Current Implementation:
- Storage mechanism: `st.session_state.compute_instances` (LIST)
- YAML generation: Pulls from session_state ✅
- Terraform generation: Pulls from session_state ✅
- Loop generation: `enumerate(..., 1)` creates vm_1, vm_2, etc. ✅

## Conclusion

The code **should** work correctly for multiple compute instances. If it doesn't:
1. Check that unique names are used
2. Verify st.session_state.compute_instances contains all instances
3. Check generated main.tf for multiple vm_X resources
4. Look for any errors in Streamlit console

The implementation uses the same pattern as other resources (storage buckets, firewall rules) which work correctly for multiple instances.
