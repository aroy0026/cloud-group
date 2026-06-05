terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  enabled_services = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "secretmanager.googleapis.com",
  ])
}

resource "google_project_service" "services" {
  for_each           = local.enabled_services
  service            = each.value
  disable_on_destroy = false
}

resource "google_storage_bucket" "processing" {
  name                        = var.processing_bucket
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  lifecycle_rule {
    condition {
      age            = 1
      matches_prefix = ["query-temp/"]
      with_state     = "ANY"
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_pubsub_topic" "media_processing" {
  name       = "media-processing"
  depends_on = [google_project_service.services]
}

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.artifact_repository
  description   = "Aussie EcoLens Cloud Run processor images"
  format        = "DOCKER"

  depends_on = [google_project_service.services]
}

resource "google_service_account" "aws_dispatcher" {
  account_id   = "aws-dispatcher-sa"
  display_name = "AWS dispatcher to GCP"

  depends_on = [google_project_service.services]
}

resource "google_service_account" "cloud_run_processor" {
  account_id   = "cloud-run-processor-sa"
  display_name = "Aussie EcoLens Cloud Run processor"

  depends_on = [google_project_service.services]
}

resource "google_service_account" "pubsub_push" {
  account_id   = "pubsub-cloudrun-push-sa"
  display_name = "Pub/Sub push invoker for Cloud Run"

  depends_on = [google_project_service.services]
}

resource "google_storage_bucket_iam_member" "dispatcher_storage" {
  bucket = google_storage_bucket.processing.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.aws_dispatcher.email}"
}

resource "google_project_iam_member" "dispatcher_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.aws_dispatcher.email}"
}

resource "google_pubsub_topic_iam_member" "dispatcher_pubsub" {
  topic  = google_pubsub_topic.media_processing.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.aws_dispatcher.email}"
}

resource "google_storage_bucket_iam_member" "processor_storage" {
  bucket = google_storage_bucket.processing.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_processor.email}"
}

resource "google_project_iam_member" "processor_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_processor.email}"
}

resource "google_cloud_run_v2_service" "processor" {
  count    = var.cloud_run_image == "" ? 0 : 1
  name     = "aussie-ecolens-processor"
  location = var.region

  template {
    service_account = google_service_account.cloud_run_processor.email
    timeout         = "900s"

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = var.cloud_run_image

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }

      env {
        name  = "GCS_BUCKET"
        value = google_storage_bucket.processing.name
      }
      env {
        name  = "MODEL_PATH"
        value = "/app/model.pt"
      }
      env {
        name  = "LABELS_PATH"
        value = "/app/labels.txt"
      }
      env {
        name  = "CONFIDENCE_THRESHOLD"
        value = var.confidence_threshold
      }
      env {
        name  = "AWS_SNS_REGION"
        value = var.aws_sns_region
      }
      env {
        name  = "AWS_NOTIFICATION_LAMBDA_URL"
        value = var.aws_notification_lambda_url
      }
    }
  }

  depends_on = [
    google_project_service.services,
    google_storage_bucket_iam_member.processor_storage,
    google_project_iam_member.processor_firestore,
  ]
}

resource "google_cloud_run_service_iam_member" "pubsub_invoker" {
  count    = var.cloud_run_image == "" ? 0 : 1
  location = google_cloud_run_v2_service.processor[0].location
  service  = google_cloud_run_v2_service.processor[0].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub_push.email}"
}

resource "google_pubsub_subscription" "cloud_run_push" {
  count = var.cloud_run_image == "" ? 0 : 1
  name  = "media-processing-cloudrun-sub"
  topic = google_pubsub_topic.media_processing.name

  ack_deadline_seconds = 600

  push_config {
    push_endpoint = google_cloud_run_v2_service.processor[0].uri

    oidc_token {
      service_account_email = google_service_account.pubsub_push.email
      audience              = google_cloud_run_v2_service.processor[0].uri
    }
  }

  depends_on = [google_cloud_run_service_iam_member.pubsub_invoker]
}

resource "google_service_account_key" "aws_dispatcher" {
  count              = var.create_dispatcher_key ? 1 : 0
  service_account_id = google_service_account.aws_dispatcher.name
}

output "processing_bucket" {
  value = google_storage_bucket.processing.name
}

output "pubsub_topic" {
  value = google_pubsub_topic.media_processing.id
}

output "artifact_repository" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}

output "processor_image_hint" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}/processor:latest"
}

output "aws_dispatcher_service_account" {
  value = google_service_account.aws_dispatcher.email
}

output "cloud_run_service_account" {
  value = google_service_account.cloud_run_processor.email
}

output "cloud_run_url" {
  value = var.cloud_run_image == "" ? "" : google_cloud_run_v2_service.processor[0].uri
}

output "aws_dispatcher_key_json_base64" {
  value     = var.create_dispatcher_key ? google_service_account_key.aws_dispatcher[0].private_key : ""
  sensitive = true
}

