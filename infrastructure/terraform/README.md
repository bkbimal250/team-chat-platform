# Infrastructure layout

GlobalChat **production compute** runs on a **Hostinger VPS** with Docker Compose (`deploy/hostinger/`).

**AWS** is limited to **private S3** for encrypted media:

- `infrastructure/aws/s3-media/` — bucket policy, IAM for VPS, optional S3-only Terraform

The former `environments/production` ECS/RDS/VPC Terraform stack has been removed from this repository. Historical state archives (if any) are operator-owned outside git.

Local Postgres/Redis/RabbitMQ: `docker-compose.local.yml` and `scripts/local/dev.py`.
