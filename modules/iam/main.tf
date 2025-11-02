# IAM Member (Non-authoritative)
resource "google_project_iam_member" "member" {
  count   = var.iam_type == "member" && var.member != null ? 1 : 0
  project = var.project_id
  role    = var.role
  member  = var.member
  dynamic "condition" {
    for_each = var.condition == null ? [] : [var.condition]
    content {
      title       = condition.value.title
      expression  = condition.value.expression
      description = try(condition.value.description, null)
    }
  }
}

# IAM Binding (Authoritative for a given role)
resource "google_project_iam_binding" "binding" {
  count   = var.iam_type == "binding" && length(var.members) > 0 ? 1 : 0
  project = var.project_id
  role    = var.role
  members = var.members
  dynamic "condition" {
    for_each = var.condition == null ? [] : [var.condition]
    content {
      title       = condition.value.title
      expression  = condition.value.expression
      description = try(condition.value.description, null)
    }
  }
}

# IAM Policy (Authoritative - replaces entire policy)
resource "google_project_iam_policy" "policy" {
  count       = var.iam_type == "policy" && var.policy_data != null ? 1 : 0
  project     = var.project_id
  policy_data = var.policy_data
}

# IAM Audit Config (Authoritative for audit logging)
resource "google_project_iam_audit_config" "audit_config" {
  count   = var.iam_type == "audit_config" && var.service != null ? 1 : 0
  project = var.project_id
  service = var.service

  dynamic "audit_log_config" {
    for_each = var.audit_log_configs
    content {
      log_type         = audit_log_config.value.log_type
      exempted_members = audit_log_config.value.exempted_members
    }
  }
}
