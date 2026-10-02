# Future gateway deployment (do not apply during ingress remediation)

After the new source freeze, Step 10A must add `globalchat/gateway`, build the gateway image from
`services/gateway-service`, record its immutable digest, and register one `gateway-api` process on
port 8008. The process uses no database, Valkey, RabbitMQ, S3, or application secrets. It receives
the seven internal URL environment variables already represented by `local.internal_urls`.

Create a new IP target group for gateway port 8008 and a gateway ECS service in private application
subnets. Keep the existing Organization target group until gateway health and routing verification
passes. Then change only the `api.michat.in` HTTPS forward action to the gateway target group.
Keep `ws.michat.in` routed directly to Realtime. Rollback is the listener action back to the retained
Organization target group. Use `/health/ready` for the gateway target-group check.

These changes require a reviewed Terraform plan and apply in the later authorized deployment step.
No AWS resource is created by this document.
