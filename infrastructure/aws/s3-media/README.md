# AWS S3 — encrypted media only

GlobalChat stores **ciphertext** in S3. The VPS runs Media Service with `MEDIA_STORAGE_BACKEND=s3`. Credentials use the standard **boto3 provider chain** (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` on the VPS, or instance role if ever used elsewhere).

## Bucket requirements

- Block all public access
- Default encryption (SSE-S3 or SSE-KMS)
- Object keys under `organizations/` (application-owned prefix)
- CORS for browser/web clients (mobile uses presigned PUT from app — still configure for web):

| Setting | Value |
|---------|--------|
| Methods | `GET`, `HEAD`, `PUT` |
| Headers | `Content-Type`, `x-amz-checksum-sha256` |
| Expose | `ETag` |
| Origins | Your `https://app…`, `https://admin…` origins |

## IAM for VPS (least privilege)

Use `iam-vps-media-policy.json`. Replace `MEDIA_BUCKET_ARN` with your bucket ARN.

1. Create IAM user `globalchat-vps-media` (no console access).
2. Attach the policy.
3. Create access keys; store only on the VPS in `.env` (not in git).

Permissions mirror production media task policy: `ListBucket`, object `Get/Put/Delete/AbortMultipartUpload` on `organizations/*` only.

## Optional Terraform

`terraform/` in this folder manages **bucket + policy documents only** (no ECS/RDS/VPC). State locally or in your own backend.

```bash
cd infrastructure/aws/s3-media/terraform
terraform init
terraform plan -var="bucket_name=your-bucket" -var='cors_allowed_origins=["https://app.example.com"]'
# terraform apply — only when you intend to create real AWS resources
```

## Verification (manual)

After deploy:

1. Initiate upload via API → PUT ciphertext to presigned URL → `POST .../complete` → status `READY`.
2. Download via `GET .../download` → presigned GET returns ciphertext only.
3. Confirm bucket has no public ACL/policy.

See `services/media-service/tests/unit/test_s3_storage.py` for expected S3 adapter behavior.
