output "region" {
  value = "ap-south-1"
}

output "state_bucket_name" {
  value = aws_s3_bucket.terraform_state.id
}
