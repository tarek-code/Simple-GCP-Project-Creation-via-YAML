resource "google_sql_database_instance" "instance" {
  name             = var.name
  project          = var.project_id
  database_version = var.database_version
  region           = var.region

  settings {
    tier = var.tier
  }
}


