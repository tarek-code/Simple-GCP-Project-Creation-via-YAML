resource "google_project_iam_member" "binding" {
  count   = length(var.members) == 0 ? 1 : 0
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

resource "google_project_iam_member" "bindings" {
  for_each = { for m in var.members : m => m }
  project  = var.project_id
  role     = var.role
  member   = each.value
  dynamic "condition" {
    for_each = var.condition == null ? [] : [var.condition]
    content {
      title       = condition.value.title
      expression  = condition.value.expression
      description = try(condition.value.description, null)
    }
  }
}


