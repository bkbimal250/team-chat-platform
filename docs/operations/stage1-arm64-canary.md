# Stage 1: ARM64 Media canary preparation

**No deployment, ECR publication or Terraform apply performed.** No application/Dockerfile changes. Plan B remains the eventual target; this stage keeps RabbitMQ, workers, data stores and network unchanged.

## Compatibility evidence

Nine current-source production images built successfully for linux/arm64. A tenth image uses exact deployed Media source `fe839197a8fcd5e06ba1e391bdd52666b345b163`, confirmed by the deployed ECR tag. Local source was `6fa5057d295c9616bf5f2bf44007d5ae8a83c798` before preparation files were added. Do not deploy current-source builds during this canary: they include pending feature-release changes.

Docker build metadata resolved ARM64 Python 3.12-slim and uv 0.12.17 bases. Production uv dependency installation succeeded on ARM64, including native asyncpg, cryptography, pydantic-core, uvloop, httptools, watchfiles and service-specific psycopg/grpc/protobuf packages where present. No application x86-specific code was found in inspected Python/Dockerfile/project configuration. Worker/outbox entrypoints share these service images; import evidence and regression results are recorded below after execution.

Builds run using Docker Desktop QEMU emulation; this proves architecture compatibility, not native Fargate throughput. Native Fargate latency/load validation remains mandatory before promotion. Existing production images/digests are unchanged. Local manifest digest must be reverified after any later approved ECR publication; no image exists at the planned ECR digest yet.

## Exact sizing / costs

See stage1-fargate-sizing.csv for all 24 processes, current/proposed CPU and memory, reason and risk. Only Media API is a resizing candidate. Keep Realtime at 0.5 vCPU/1024 MiB for WebSocket headroom. Gateway/authentication and every Rabbit consumer/outbox retain their current allocations. Twenty-two tasks are already minimum-sized.

Current Fargate modeled monthly compute: **$246.12**. After an approved successful Media-only ARM64/0.25-vCPU/512-MiB promotion: **$232.49**, saving **$13.63/month**. Preparation changes actual compute cost by zero. An additive canary costs about **$0.007262/hour** while running; it does not replace baseline and initially adds cost. Do not report eventual fleet-wide Plan A savings as Stage-1 savings. Rates and assumptions are inherited from the completed Mumbai audit (730 hours, no free tier/credits).

## First canary: Media API

- Baseline: `arn:aws:ecs:ap-south-1:167667034490:task-definition/globalchat-production-media-api:1`, X86_64, 512 CPU units / 1024 MiB.
- Baseline immutable image: `167667034490.dkr.ecr.ap-south-1.amazonaws.com/globalchat/media@sha256:3485c018a724aba930c1540b091528bbee950ccab0ef6930fe97cb822bd25669`.
- Local ARM64 candidate: `globalchat/media:arm64-git-fe839197a8fc`, manifest `sha256:a2fc7b29e4e228f5c632eab2cd581ac5664d3f19ad44f6787645fff56b8e94c0`.
- Canary: new task-definition family globalchat-production-media-arm64-canary, ARM64, 256 CPU units / 512 MiB. Same command, port 8005, production environment, secret ARN selectors, execution role and Media task role are copied from the pinned baseline. No secret values retrieved.
- Definition plus a paused canary ECS service (desired_count=0): no task run, Cloud Map registration, target-group registration, public IP, public hostname, DNS or ALB rule. Production Media remains the sole existing Cloud Map endpoint. Gateway routing remains untouched.
- A separately approved activation changes only the isolated canary service desired count from zero to one. It uses the existing cluster/private app subnets/ECS security group, Fargate platform 1.4.0, assignPublicIp DISABLED. Do not create probing infrastructure, enable ECS Exec without required permissions, or point public requests at the canary.
- Readiness health check: container-local GET /health/ready, timeout three seconds, interval 30, task check timeout five, three retries, 60-second startup grace. Verify /health/live and readiness behavior with controlled private/local probes; never bypass authentication for application metadata.
- CloudWatch: existing /globalchat/production/media group, distinct media-arm64-canary stream prefix. Inspect startup/native import/config/dependency errors, ECS container health/exit reason and task restarts. Container Insights is disabled and remains unchanged. After approved activation, standard AWS/ECS CPUUtilization and MemoryUtilization use ClusterName=globalchat-production and ServiceName=globalchat-production-media-arm64-canary. These service metrics support the sizing thresholds without paid Container Insights. No utilization data exists before activation.

## Acceptance and rollback

Future approval gates: publish the verified source-matched ARM image to existing Media ECR; verify registry manifest architecture/digest; regenerate/review the two-resource plan; approve apply; approve the isolated private service activation. Nothing in this repository task performs those actions.

Observe 30â€“60 minutes, plus representative controlled read-only signing/metadata load against authorized fixtures. No uploads, DB writes, OTP/SMS/FCM, or real credentials in logs. Compare to the existing x86 baseline under the same request rate. Do not use QEMU timing as the production baseline.

Acceptance: HEALTHY within 180 seconds, live/ready sustained 200; zero crashes, OOM, secret-injection/config errors or unexpected writes; no public IP/registration; p95 latency no more than 20% worse than x86 and within the existing service SLO. CPU >70% for ten minutes or memory >75% for five minutes fails the reduced-size gate **where measured by verified task telemetry**. If telemetry/load evidence is unavailable, promotion is blocked.

Rollback immediately for unhealthy startup, any OOM/crash/restart loop, native import/illegal-instruction failure, repeated readiness/dependency errors, auth/tenant regression or unexplained error increase. The isolated canary never owns production routing, so return only its desired count to zero through a separately approved Terraform change and retain the baseline task/digest. No baseline replacement is needed. A later production promotion must keep the captured x86 definition and image available and restore them if the same criteria fail. Do not deregister or delete rollback definitions/images.

## Terraform isolation

Root: infrastructure/terraform/canaries/media-arm64. Separate state key production/canaries/media-arm64.tfstate in the existing production state bucket. It reads only the pinned deployed Media task-definition metadata, not production Terraform state/secret values. This avoids mixing 23 pending feature-release task revisions into the canary plan. It introduces no new network/data/IAM dependency or routing change. The additional service is explicitly paused; neither resource is applied and no task is started.

Plan must be exactly **two resources to add (one task definition and one desired-zero service), zero to change/destroy**. Registration remains unapplied and the candidate image remains local. Mock Terraform plan test asserts ARM sizing, unchanged environment/command/secret selectors, immutable rollback references and health/log isolation.

Commands: terraform init; terraform fmt -check -recursive; terraform validate; terraform test; terraform plan -var-file=stage1.tfvars -out=stage1.tfplan. The local tfvars is ignored and pins the locally verified candidate digest; publication approval/readback is required before applying. No -target or ignore_changes workaround.

[AWS ARM64 Fargate support](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-arm64.html), [Docker multi-platform builds](https://docs.docker.com/build/building/multi-platform/).

## Executed validation

All nine service ARM64 runtime checks and the source-matched Media canary passed, including native extension imports and RSA sign/verify where available. All worker/outbox implementations imported successfully; entrypoint wrappers that start a worker unconditionally were not executed. Initial harness import-path/settings-fixture errors were corrected and the affected checks rerun successfully. No running worker connected to a production broker.

Current-source regression: 361 passed, zero failed. One local live Rabbit integration test was explicitly deselected because the broker is unavailable; it is not claimed as passing. Source-matched Media suite inside the ARM64 container: 39 passed, zero failed. Terraform fmt, validate and the plan-based test passed. Reviewed plan: two additions only, zero changes/deletions; canary service desired count zero.

Preparation is complete; execution is gated on approved image publication/readback, apply and isolated activation. No native Fargate performance or live canary result is claimed.
