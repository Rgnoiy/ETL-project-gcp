provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# set up a vm
resource "google_compute_instance" "vm_instance" {
  name         = "instance-3392"
  machine_type = "e2-medium"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    # A default network is created for all GCP projects
    network = "default"
  }

  service_account {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    email  = "305781237272-compute@developer.gserviceaccount.com"
    scopes = ["cloud-platform"]
  }
}


####################################################################################
# CREATE BUCKET
####################################################################################

# Create a bucket in EU
resource "google_storage_bucket" "trigger-bucket" {
  name          = "cafe-etl-raw-data-bucket-csv0001"
  location      = "EU"
  force_destroy = true
  storage_class = "MULTI_REGIONAL"
  uniform_bucket_level_access = true
}

####################################################################################
# CREATE FUNCTION
####################################################################################

resource "google_storage_bucket" "source-bucket" {
  name     = "gcf-source-code-bucket"
  location = "EU"
  force_destroy = true
  storage_class = "MULTI_REGIONAL"
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_object" "object" {
  name   = "function_source.zip"
  bucket = google_storage_bucket.source-bucket.name
  source = "./function_source.zip"
}

resource "google_cloudfunctions2_function" "function" {
  name = "csv-transaction-function"
  location = var.region
  description = "a new function"

  build_config {
    runtime     = "python310"
    entry_point = "data_transformation" # Set the entry point in the code
    source {
      storage_source {
        bucket = google_storage_bucket.source-bucket.name
        object = google_storage_bucket_object.object.name
      }
    }
  }

  service_config {
    min_instance_count = 1
    available_memory    = "512M"
    timeout_seconds     = 300
    ingress_settings    = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true
    service_account_email = var.service_account_email
  }

  event_trigger {
    trigger_region = "eu"
    event_type = "google.cloud.storage.object.v1.finalized"
    retry_policy = "RETRY_POLICY_DO_NOT_RETRY"
    service_account_email = var.service_account_email
    event_filters {
      attribute = "bucket"
      value = google_storage_bucket.trigger-bucket.name
    }
  }
}

####################################################################################
# CREATE BIGQUERY DATASET
####################################################################################


resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = "cafe_transformed_data"
  location                    = "EU"

  labels = {
    env = "default"
  }

  access {
    role          = "OWNER"
    user_by_email = var.service_account_email
  }

  access {
    role          = "OWNER"
    user_by_email = "miaaayi55@gmail.com"
  }

  access {
    role   = "READER"
    domain = "cafe.com"
  }
}