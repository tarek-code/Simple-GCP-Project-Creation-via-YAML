terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.4.0"
    }
  }
}

provider "google" {
  project = var.project_id
}

module "project" {
  source          = "../../modules/project"
  project_id      = var.project_id
  organization_id = var.organization_id
  billing_account = var.billing_account
  labels          = var.labels
  apis            = var.apis
  create_project  = true
}


# Additional resources from YAML
module "service_account_1" {
  source  = "../../modules/service_account"
  project_id   = var.project_id
  account_id   = "pubsub-service-account"
  display_name = "Pub/Sub Service Account"
  description  = "Service account for Pub/Sub operations"
}

module "pubsub_topic_1" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "user-events"
  labels  = {"env": "dev", "service": "user-management", "purpose": "events"}
  subscriptions = []
}

module "pubsub_topic_2" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "order-processing"
  labels  = {"env": "dev", "service": "e-commerce", "purpose": "orders"}
  subscriptions = [{"name": "inventory-service", "ack_deadline_seconds": 60, "retain_acked_messages": true, "message_retention_duration": "604800s", "description": "Inventory management service"}, {"name": "payment-service", "ack_deadline_seconds": 120, "retain_acked_messages": false, "message_retention_duration": "86400s", "description": "Payment processing service"}, {"name": "shipping-service", "ack_deadline_seconds": 300, "retain_acked_messages": true, "message_retention_duration": "1209600s", "description": "Shipping and logistics service"}]
}

module "pubsub_topic_3" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "notifications"
  labels  = {"env": "dev", "service": "notification-system", "purpose": "alerts"}
  subscriptions = [{"name": "email-notifications", "push_endpoint": "https://email-service.example.com/webhook", "oidc_service_account_email": "pubsub-service-account@dev-intern-poc.iam.gserviceaccount.com", "oidc_audience": "email-service-audience", "ack_deadline_seconds": 30, "retry_min_backoff": "10s", "retry_max_backoff": "300s", "description": "Email notification service"}, {"name": "sms-notifications", "push_endpoint": "https://sms-service.example.com/webhook", "oidc_service_account_email": "pubsub-service-account@dev-intern-poc.iam.gserviceaccount.com", "oidc_audience": "sms-service-audience", "ack_deadline_seconds": 30, "retry_min_backoff": "5s", "retry_max_backoff": "600s", "description": "SMS notification service"}]
}

module "pubsub_topic_4" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "sensor-data"
  labels  = {"env": "dev", "service": "iot-platform", "purpose": "telemetry"}
  subscriptions = [{"name": "temperature-monitoring", "filter": "attributes.sensor_type=\"temperature\"", "ack_deadline_seconds": 60, "message_retention_duration": "2592000s", "description": "Temperature sensor data processing"}, {"name": "humidity-monitoring", "filter": "attributes.sensor_type=\"humidity\"", "ack_deadline_seconds": 60, "message_retention_duration": "2592000s", "description": "Humidity sensor data processing"}, {"name": "alert-service", "filter": "attributes.value>80 OR attributes.value<10", "ack_deadline_seconds": 30, "retry_min_backoff": "5s", "retry_max_backoff": "60s", "description": "Alert service for critical values"}]
}

module "pubsub_topic_5" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "critical-tasks"
  labels  = {"env": "dev", "service": "task-processor", "purpose": "critical-workflows"}
  subscriptions = [{"name": "task-processor", "dead_letter_topic": "failed-tasks", "max_delivery_attempts": 3, "ack_deadline_seconds": 300, "retry_min_backoff": "10s", "retry_max_backoff": "600s", "description": "Main task processing service"}, {"name": "backup-processor", "dead_letter_topic": "failed-tasks", "max_delivery_attempts": 5, "ack_deadline_seconds": 600, "retry_min_backoff": "30s", "retry_max_backoff": "1800s", "description": "Backup task processing service"}]
}

module "pubsub_topic_6" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "failed-tasks"
  labels  = {"env": "dev", "service": "error-handling", "purpose": "dead-letters"}
  subscriptions = [{"name": "error-logger", "ack_deadline_seconds": 60, "message_retention_duration": "1209600s", "description": "Log failed tasks for analysis"}, {"name": "admin-notifications", "push_endpoint": "https://admin-alerts.example.com/webhook", "oidc_service_account_email": "pubsub-service-account@dev-intern-poc.iam.gserviceaccount.com", "oidc_audience": "admin-alerts-audience", "ack_deadline_seconds": 30, "description": "Notify administrators of failed tasks"}]
}

module "pubsub_topic_7" {
  source  = "../../modules/pubsub"
  project_id = var.project_id
  name    = "temporary-data"
  labels  = {"env": "dev", "service": "data-processing", "purpose": "temporary-storage"}
  subscriptions = [{"name": "data-processor", "expiration_policy_ttl": "86400s", "ack_deadline_seconds": 60, "message_retention_duration": "86400s", "description": "Process temporary data with short TTL"}]
}
