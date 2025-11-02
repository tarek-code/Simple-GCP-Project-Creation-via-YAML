resource "google_pubsub_topic" "topic" {
  name    = var.name
  project = var.project_id
  labels  = var.labels
}

resource "google_pubsub_subscription" "subs" {
  for_each = { for s in var.subscriptions : s.name => s }
  name     = each.value.name
  project  = var.project_id
  topic    = google_pubsub_topic.topic.name

  ack_deadline_seconds       = try(each.value.ack_deadline_seconds, null)
  retain_acked_messages      = try(each.value.retain_acked_messages, null)
  message_retention_duration = try(each.value.message_retention_duration, null)
  filter                     = try(each.value.filter, null)

  dynamic "dead_letter_policy" {
    for_each = try(each.value.dead_letter_topic, null) == null ? [] : [1]
    content {
      dead_letter_topic     = each.value.dead_letter_topic
      max_delivery_attempts = try(each.value.max_delivery_attempts, null)
    }
  }

  dynamic "push_config" {
    for_each = try(each.value.push_endpoint, null) == null ? [] : [1]
    content {
      push_endpoint = each.value.push_endpoint
      oidc_token {
        service_account_email = try(each.value.oidc_service_account_email, null)
        audience              = try(each.value.oidc_audience, null)
      }
    }
  }

  dynamic "expiration_policy" {
    for_each = try(each.value.expiration_policy_ttl, null) == null ? [] : [1]
    content {
      ttl = each.value.expiration_policy_ttl
    }
  }

  dynamic "retry_policy" {
    for_each = (try(each.value.retry_min_backoff, null) == null && try(each.value.retry_max_backoff, null) == null) ? [] : [1]
    content {
      minimum_backoff = try(each.value.retry_min_backoff, null)
      maximum_backoff = try(each.value.retry_max_backoff, null)
    }
  }
}


