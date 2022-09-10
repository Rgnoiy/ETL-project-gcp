provider "google" {
  credentials = "${secrets.GCP_MAIN_SERVICE_ACCOUNT_SECRET_KEY}"
  project = "glass-haven-360720"
  region  = "eu-west2"
  zone    = "eu-west2-a"
}

# Creates a Google Service Account.
resource "google_service_account" "service_account" {
  account_id   = "svc-bucket"
  display_name = "My Pipline Storage SA"
}

# Assign role to service account.
resource "google_project_iam_member" "storage" {
  project = "glass-haven-360720"
  role    = [
    "roles/storage.admin",
    "roles/
  member  = "serviceAccount:${google_service_account.service_account.email}"
}

# Create a bucket
resource "google_storage_bucket" "bucket" {
  name          = "raw-data-bucket-csv0003"
  location      = "EU"
  force_destroy = true
}

# Associate service account with bucket
resource "google_storage_bucket_access_control" "public_rule" {
  bucket = google_storage_bucket.bucket.name
  entity = "OWNER:${google_service_account.service_account.email}"
}
