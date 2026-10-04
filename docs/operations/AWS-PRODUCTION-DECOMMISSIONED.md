# Current AWS production: decommissioned

2026-10-04: owner authorized complete GlobalChat production decommission in account 167667034490, region ap-south-1.

**DO NOT RUN NORMAL TERRAFORM APPLY against the old production root.** Its retained state/source references deleted resources and a normal plan/apply can recreate production. No replacement production environment is authorized.

Production and bootstrap state copies, repository history, immutable image references and old architecture metadata were preserved in the ACL-protected local retirement archive outside Git. The remote state bucket is temporarily retained for verification; no Terraform apply/destroy has been executed. Direct AWS deletion was expressly authorized; retained remote Terraform state is stale and must be reviewed through read-only inventory before any future rebuild/state migration. No deletion of the backend or blind state removal is authorized.

GlobalChat is returning to local development. Application/local source and unrelated project resources are unchanged. Final inventory confirms no GlobalChat running ECS services/tasks, MQ/cache/RDS instances or snapshots, ALB/NAT/EIP/VPC/endpoints, ECR, media bucket or production logs remain. Secrets are scheduled for deletion; the state bucket and no-cost IAM/OIDC/ACM metadata remain. The public michat.in hosted zone was already missing before this task; it was not recreated. Final deletion results are recorded in the local decommission report. Domain registrar, ACM certificate, GitHub OIDC/deployment role and retained state bucket must be verified independently before any future production rebuild.
