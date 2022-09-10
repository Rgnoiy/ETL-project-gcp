provider "google" {
  credentials = "${secrets.GCP_MAIN_SERVICE_ACCOUNT_SECRET_KEY}"
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Create a Google Service Account.
resource "google_service_account" "service_account" {
  account_id   = var.service_account_id
  display_name = "A service account for Mia"
  email = var.service_account_email
}

# attach roles to service account.
resource "google_service_account_iam_member" "service_account_role" {
  service_account_id = google_service_account.service_account.account_id
  role               = "roles/serviceAccountTokenCreator"
  member             = google_service_account.service_account.email
} 

# create a key for service account
resource "google_service_account_key" "mykey" {
  service_account_id = google_service_account.service_account.account_id
}

# store key in k8s secret
resource "kubernetes_secret" "google-application-credentials" {
  metadata {
    name = "google-application-credentials"
  }
  data = {
    "credentials.json" = base64decode(google_service_account_key.mykey.private_key)
  }
}



####################################################################################
# CREATE BUCKET
####################################################################################

# Assign service account storage Admin role.
resource "google_service_account_iam_member" "storage" {
  service_account_id = google_service_account.service_account.account_id
  role               = "roles/storageAdmin"
  member             = google_service_account.service_account.email
} 

# Assign service account with storage Admin role.
resource "google_service_account_iam_member" "storage" {
  service_account_id = google_service_account.service_account.account_id
  role               = "roles/storageObjectAdmin"
  member             = google_service_account.service_account.email
} 

# Create a bucket in EU
resource "google_storage_bucket" "bucket" {
  name          = "cafe-etl-raw-data-bucket-csv0001"
  location      = "EU"
  force_destroy = true
  storage_class = "MULTI_REGIONAL"
  uniform_bucket_level_access = true
}

# Associate service account with bucket
resource "google_storage_bucket_access_control" "public_rule" {
  bucket = google_storage_bucket.bucket.name
  entity = "OWNER:${google_service_account.service_account.email}"
}
