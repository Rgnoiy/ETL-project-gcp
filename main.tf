terraform {
  required_providers {
    gcp = {
      source = "hashicorp/google"
    }
    random = {
      source = "hashicorp/random"
    }
  }

  cloud {
    organization = "miayi_organization"

    workspaces {
      name = "ETL-project-gcp-appsbroker"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# set up a vm
resource "google_compute_instance" "vm_instance" {
  name         = "instance-222"
  machine_type = "e2-medium"

  boot_disk {
    initialize_params {
      image = "ubuntu-1804-bionic-v20220824"
    }
  }

  network_interface {
    # A default network is created for all GCP projects
    network = "default"
    access_config {
    }
  }
}

resource "google_compute_network" "vpc_network" {
  name                    = "terraform-network"
  auto_create_subnetworks = "true"
}

# Create a Google Service Account.
resource "google_service_account" "service_account" {
  account_id   = var.service_account_id
  display_name = "A service account for Mia"
}

# attach roles to service account.
resource "google_service_account_iam_member" "service_account_roles" {
  service_account_id = "${var.project_name}/${var.project_id}/${var.service_account_id}/${google_service_account.service_account.email}"
  for_each = toset([
    "roles/iam.serviceAccountTokenCreator",
	"roles/storage.admin",
	"roles/cloudfunctions.admin",
	"roles/bigquery.admin",
	"roles/eventarc.eventReceiver"
  ])
  role               = each.key
  member             = "serviceAccount:${google_service_account.service_account.email}"
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
