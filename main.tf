# terraform {
#   required_providers {
#     gcp = {
#       source = "hashicorp/google"
#     }
#     random = {
#       source = "hashicorp/random"
#     }
#   }

#   cloud {
#     organization = "miayi_organization"

#     workspaces {
#       name = "ETL-project-gcp-appsbroker"
#     }
#   }
# }

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# set up a vm
# resource "google_compute_instance" "vm_instance" {
#   name         = "instance-3392"
#   machine_type = "e2-medium"
#   zone         = var.zone

#   boot_disk {
#     initialize_params {
#       image = "debian-cloud/debian-11"
#     }
#   }

#   network_interface {
#     # A default network is created for all GCP projects
#     network = "default"
#   }

#   service_account {
#     # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
#     email  = "305781237272-compute@developer.gserviceaccount.com"
#     scopes = ["cloud-platform"]
#   }
# }



####################################################################################
# CREATE SERVICE ACCOUNT
####################################################################################

# # Create a Google Service Account.
# resource "google_service_account" "service_account" {
#   account_id   = var.service_account_id
#   display_name = "A service account for Mia"
# }

# # attach roles to service account.
# resource "google_service_account_iam_member" "service_account_roles" {
#   service_account_id = "${var.project_name}/${var.project_id}/${var.service_account_id}/${google_service_account.service_account.email}"
#   for_each = toset([
#     "iam.serviceAccountTokenCreator",
#     "iam.serviceAccountKeys.create",
# 	  "storage.admin",
# 	  "cloudfunctions.admin",
# 	  "bigquery.admin",
#     "pubsub.Admin",
# 	  "eventarc.eventReceiver",
#     "run.invoker",
#     "artifactregistry.reader",
#   ])
#   role               = each.key
#   member             = "serviceAccount:${google_service_account.service_account.email}"
# } 

# # create a key for service account
# resource "google_service_account_key" "mykey" {
#   service_account_id = google_service_account.service_account.account_id
# }

# # store key in k8s secret
# resource "kubernetes_secret" "google-application-credentials" {
#   metadata {
#     name = "google-application-credentials"
#   }
#   data = {
#     "credentials.json" = base64decode(google_service_account_key.mykey.private_key)
#   }
# }



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

# Associate service account with bucket
# resource "google_storage_bucket_access_control" "public_rule" {
#   bucket = google_storage_bucket.trigger-bucket.name
#   role   = "OWNER"
#   entity = "${google_service_account.service_account.email}"
# }



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

# resource "google_storage_bucket_access_control" "public_rule1" {
#   bucket = google_storage_bucket.source-bucket.name
#   entity = "OWNER:${google_service_account.service_account.email}"
# }

# resource "google_project_iam_member" "gcs-pubsub-publishing" {
#   project = "my-project-name"
#   role    = "roles/pubsub.publisher"
#   member  = "serviceAccount:${var.service_account_email}"
# }

# resource "google_project_iam_member" "invoking" {
#   project = var.project_id
#   role    = "roles/run.invoker"
#   member  = "serviceAccount:${var.service_account_email}"
#   depends_on = [google_project_iam_member.gcs-pubsub-publishing]
# }

# resource "google_project_iam_member" "event-receiving" {
#   project = var.project_id
#   role    = "roles/eventarc.eventReceiver"
#   member  = "serviceAccount:${var.service_account_email}"
#   depends_on = [google_project_iam_member.invoking]
# }

# resource "google_project_iam_member" "artifactregistry-reader" {
#   project = var.project_id
#   role     = "roles/artifactregistry.reader"
#   member   = "serviceAccount:${var.service_account_email}"
#   depends_on = [google_project_iam_member.event-receiving]
# }

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

resource "google_storage_bucket_object" "object" {
  name   = "function-source.zip"
  bucket = google_storage_bucket.source-bucket.name
  source = "./function-source.zip"  
}

####################################################################################
# CREATE BIGQUERY DATASET
####################################################################################


resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = "transformed_data_for_cafe"
  description                 = "This dataset is private"
  location                    = "EU"
  default_table_expiration_ms = 3600000

  labels = {
    env = "default"
  }

  access {
    role          = "OWNER"
    user_by_email = var.service_account_email
  }

  access {
    role   = "READER"
    domain = "cafe.com"
  }
}