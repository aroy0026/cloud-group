variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "region" {
  type    = string
  default = "australia-southeast1"
}

variable "processing_bucket" {
  type        = string
  description = "Globally unique GCS bucket name for processing/originals/thumbnails."
}

variable "artifact_repository" {
  type    = string
  default = "aussie-ecolens"
}

variable "cloud_run_image" {
  type        = string
  default     = ""
  description = "Full Artifact Registry image URL. Leave empty for first pass before the image exists."
}

variable "confidence_threshold" {
  type    = string
  default = "0.20"
}

variable "aws_sns_region" {
  type    = string
  default = "ap-southeast-2"
}

variable "aws_notification_lambda_url" {
  type        = string
  default     = ""
  description = "Optional Lambda Function URL if Cloud Run publishes notifications through AWS."
}

variable "create_dispatcher_key" {
  type        = bool
  default     = true
  description = "Create a JSON key for the AWS dispatcher service account so it can be stored in AWS Secrets Manager."
}
