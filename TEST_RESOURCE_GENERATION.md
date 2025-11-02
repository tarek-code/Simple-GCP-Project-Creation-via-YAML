# Test Plan: Verify All Resources Appear in Generated Files

## The Fix
Modified both YAML and Terraform generation to pull resources directly from `st.session_state` instead of the local `resources` variable.

## Test Scenarios

### Scenario 1: Test Storage Buckets
1. Open the Streamlit app
2. Go to "Project Builder" page
3. Fill in Project ID: `test-project-123`
4. Check "🪣 Create Storage Buckets"
5. Add a bucket with name: `my-test-bucket`
6. Click "Generate Terraform Files"
7. **Expected**: `google_storage_bucket.bucket_1` appears in main.tf

### Scenario 2: Test Multiple Resources (VPC + Storage)
1. Check "🌐 Create VPC Networks"
2. Configure VPC with name: `my-vpc`
3. Check "🪣 Create Storage Buckets"
4. Add bucket with name: `my-bucket`
5. Click "Generate Terraform Files"
6. **Expected**: Both `google_compute_network.vpc_1` AND `google_storage_bucket.bucket_1` appear

### Scenario 3: Test Unchecked Checkbox (The Bug)
1. Check "🪣 Create Storage Buckets"
2. Add bucket: `my-bucket`
3. **UNCHECK** "🪣 Create Storage Buckets" (hide the form)
4. Click "Generate Terraform Files"
5. **Expected**: `google_storage_bucket.bucket_1` STILL appears
6. **Before Fix**: Bucket would NOT appear ❌
7. **After Fix**: Bucket DOES appear ✅

### Scenario 4: Test All Resource Types
Configure at least one of each resource type:
- VPC Networks
- Subnets
- Firewall Rules
- Service Accounts
- Compute Instances
- Storage Buckets
- Cloud Run Services
- Cloud SQL Instances
- Pub/Sub Topics
- Secret Manager Secrets
- BigQuery Datasets
- Artifact Registry
- DNS Zones
- Cloud Functions
- Static IPs
- Persistent Disks
- Redis Instances
- VPC Connectors
- IAM Policies

Click "Generate Terraform Files"
**Expected**: ALL configured resources appear in main.tf

### Scenario 5: Test YAML Generation
1. Configure multiple resources (VPC, Storage, Compute)
2. Click "Generate YAML Configuration"
3. **Expected**: All resources appear in the YAML under `resources:` section

## Code Changes Summary

### File: gui/streamlit_app.py

#### Change 1: YAML Generation (lines 4346-4388)
**Before:**
```python
config["resources"] = resources  # Uses local var (only checked boxes)
```

**After:**
```python
# Build resources from session state regardless of checkbox state
resources_from_state = {}
if st.session_state.get("vpcs"):
    resources_from_state["vpcs"] = st.session_state.vpcs
# ... all 19 resource types ...
config["resources"] = resources_from_state
```

#### Change 2: Terraform Generation (lines 4458-4500)
**Before:**
```python
config["resources"] = resources or {}  # Uses local var (only checked boxes)
```

**After:**
```python
# Build resources from session state regardless of checkbox state
resources_from_state = {}
if st.session_state.get("vpcs"):
    resources_from_state["vpcs"] = st.session_state.vpcs
# ... all 19 resource types ...
config["resources"] = resources_from_state
```

## How to Test

1. Start the Streamlit app:
```bash
cd /media/mario/NewVolume/Simple-GCP-Project-Creation-via-YAML/gui
streamlit run streamlit_app.py
```

2. Run through each test scenario above

3. Verify that:
   - Resources appear when checkboxes are checked ✅
   - Resources STILL appear when checkboxes are unchecked ✅
   - All 19 resource types work correctly ✅

## Expected Behavior

### Checkboxes are now UI toggles:
- **Checked**: Show configuration form
- **Unchecked**: Hide configuration form
- **Data**: Persists in `st.session_state` regardless

### File Generation:
- Always includes ALL resources from `st.session_state`
- Checkbox state doesn't affect generation
- Clean, predictable behavior

## Success Criteria

✅ All configured resources appear in generated files
✅ Checkbox state doesn't affect resource inclusion
✅ YAML and Terraform both work correctly
✅ No Python errors or exceptions
✅ Generated Terraform syntax is valid
