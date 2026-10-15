# Current AWS production: decommissioned

2026-10-04: owner authorized complete GlobalChat production decommission in account 167667034490, region ap-south-1.

**DO NOT RUN NORMAL TERRAFORM APPLY against the old production root.** Its retained state/source references deleted resources and a normal plan/apply can recreate production. No replacement production environment is authorized.

Production and bootstrap state copies, repository history, immutable image references and old architecture metadata were preserved in the ACL-protected local retirement archive outside Git. The remote state bucket is temporarily retained for verification; no Terraform apply/destroy has been executed. Direct AWS deletion was expressly authorized; retained remote Terraform state is stale and must be reviewed through read-only inventory before any future rebuild/state migration. No deletion of the backend or blind state removal is authorized.

GlobalChat production target is **Hostinger VPS + Docker Compose** (`deploy/hostinger/`). **AWS S3** remains for encrypted media only (`infrastructure/aws/s3-media/`). Legacy ECS/RDS/VPC Terraform has been removed from the repository; any remote Terraform state buckets or IAM roles in AWS are operator-owned and must be reviewed separately before reuse.
