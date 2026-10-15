variable "aws_region" {
  type        = string
  description = "AWS region for the media bucket"
  default     = "ap-south-1"
}

variable "bucket_name" {
  type        = string
  description = "Globally unique S3 bucket name for encrypted media"
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "HTTPS origins allowed to PUT/GET via presigned URLs"
}
