variable "aws_region" {
  type    = string
  default = "ap-southeast-2"
}

variable "project_name" {
  type    = string
  default = "aussie-ecolens"
}

variable "upload_bucket" {
  type        = string
  description = "Globally unique S3 bucket name for browser uploads."
}

variable "frontend_origin" {
  type        = string
  default     = "http://localhost:5173"
  description = "Frontend origin allowed by S3/API CORS."
}

variable "cognito_user_pool_id" {
  type        = string
  default     = "ap-southeast-2_y1ddoO0pv"
  description = "Existing Cognito user pool ID."
}

variable "cognito_client_id" {
  type        = string
  default     = "22jl47515ubj2b3ib3j8qm2o6i"
  description = "Existing Cognito public SPA app client ID."
}

variable "gcp_secret_id" {
  type        = string
  default     = "gcp-firestore-service-account"
  description = "AWS Secrets Manager secret name containing the GCP service account JSON."
}

variable "gcp_secret_arn" {
  type        = string
  default     = ""
  description = "Optional exact ARN for the GCP service account secret. Empty allows Secrets Manager read broadly for coursework simplicity."
}

variable "gcp_bucket" {
  type        = string
  description = "GCP Cloud Storage bucket used by the processor."
}

variable "gcp_project_id" {
  type        = string
  description = "GCP project ID."
}

variable "pubsub_topic" {
  type        = string
  description = "Full Pub/Sub topic path, e.g. projects/PROJECT_ID/topics/media-processing."
}

variable "query_file_processor_url" {
  type        = string
  default     = ""
  description = "Cloud Run /query-file URL. Set after GCP Cloud Run deploy."
}

variable "notification_tags" {
  type    = list(string)
  default = ["dingo", "felis_catus", "sus_scrofa", "casuarius_casuarius"]
}

