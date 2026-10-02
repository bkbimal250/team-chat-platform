output "region" {
  value = "ap-south-1"
}

output "state_bucket_name" {
  value = local.state_bucket_name
}

output "github_deployment_role_arn" {
  value = aws_iam_role.github_deploy.arn
}

output "github_repository_restriction" {
  value = "repo:${local.github_repository}:ref:refs/heads/${local.deployment_branch}"
}

output "vpc_id" {
  value = aws_vpc.globalchat.id
}

output "public_subnet_ids" {
  value = [for key in sort(keys(aws_subnet.public)) : aws_subnet.public[key].id]
}

output "private_app_subnet_ids" {
  value = [for key in sort(keys(aws_subnet.private_app)) : aws_subnet.private_app[key].id]
}

output "private_data_subnet_ids" {
  value = [for key in sort(keys(aws_subnet.private_data)) : aws_subnet.private_data[key].id]
}

output "alb_security_group_id" {
  value = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  value = aws_security_group.ecs.id
}

output "rds_security_group_id" {
  value = aws_security_group.rds.id
}

output "redis_security_group_id" {
  value = aws_security_group.redis.id
}

output "rabbitmq_security_group_id" {
  value = aws_security_group.rabbitmq.id
}

output "nat_gateway_id" {
  value = aws_nat_gateway.globalchat.id
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.globalchat.name
}

output "ecs_cluster_arn" {
  value = aws_ecs_cluster.globalchat.arn
}

output "cloud_map_namespace_id" {
  value = aws_service_discovery_private_dns_namespace.globalchat.id
}

output "cloud_map_namespace_name" {
  value = aws_service_discovery_private_dns_namespace.globalchat.name
}

output "ecr_repository_urls" {
  value = {
    for service, repository in aws_ecr_repository.backend : service => repository.repository_url
  }
}

output "cloudwatch_log_group_names" {
  value = {
    for service, log_group in aws_cloudwatch_log_group.backend : service => log_group.name
  }
}

output "ecs_task_execution_role_arn" {
  value = aws_iam_role.ecs_task_execution.arn
}

output "public_hosted_zone_id" {
  value = aws_route53_zone.michat.zone_id
}

output "public_hosted_zone_nameservers" {
  value = aws_route53_zone.michat.name_servers
}

output "acm_certificate_arn" {
  value = aws_acm_certificate.michat.arn
}

output "alb_arn" {
  value = aws_lb.globalchat.arn
}

output "alb_dns_name" {
  value = aws_lb.globalchat.dns_name
}

output "alb_zone_id" {
  value = aws_lb.globalchat.zone_id
}

output "api_target_group_arn" {
  value = aws_lb_target_group.api.arn
}

output "realtime_target_group_arn" {
  value = aws_lb_target_group.realtime.arn
}

output "https_listener_arn" {
  value = aws_lb_listener.https.arn
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "rds_port" {
  value = aws_db_instance.postgres.port
}

output "rds_instance_identifier" {
  value = aws_db_instance.postgres.identifier
}

output "rds_subnet_group" {
  value = aws_db_subnet_group.globalchat.name
}

output "rds_engine_version" {
  value = aws_db_instance.postgres.engine_version_actual
}

output "cache_engine" {
  value = aws_elasticache_replication_group.globalchat.engine
}

output "cache_engine_version" {
  value = aws_elasticache_replication_group.globalchat.engine_version_actual
}

output "cache_primary_endpoint" {
  value = aws_elasticache_replication_group.globalchat.primary_endpoint_address
}

output "cache_port" {
  value = aws_elasticache_replication_group.globalchat.port
}

output "cache_subnet_group" {
  value = aws_elasticache_subnet_group.globalchat.name
}

output "rabbitmq_broker_id" {
  value = aws_mq_broker.globalchat.id
}

output "rabbitmq_broker_arn" {
  value = aws_mq_broker.globalchat.arn
}

output "rabbitmq_engine_version" {
  value = aws_mq_broker.globalchat.engine_version
}

output "rabbitmq_deployment_mode" {
  value = aws_mq_broker.globalchat.deployment_mode
}

output "rabbitmq_instance_type" {
  value = aws_mq_broker.globalchat.host_instance_type
}

output "rabbitmq_amqps_endpoint" {
  value = aws_mq_broker.globalchat.instances[0].endpoints[0]
}

output "rabbitmq_port" {
  value = 5671
}

output "rabbitmq_secret_arn" {
  value = aws_secretsmanager_secret.rabbitmq_connection.arn
}

output "media_bucket_name" {
  value = aws_s3_bucket.media.id
}

output "media_bucket_arn" {
  value = aws_s3_bucket.media.arn
}

output "media_task_role_arn" {
  value = aws_iam_role.media_task.arn
}

output "service_configuration_manifest" {
  description = "Step 10 ECS environment, secret-reference, process, port, health, and task-role manifest"
  value       = local.service_configuration
}

output "application_secret_arns" {
  description = "GlobalChat application secret containers; values are never output"
  value       = { for key, secret in aws_secretsmanager_secret.application : key => secret.arn }
}

output "deployment_process_manifest" {
  description = "Step 10 source of truth for all executable GlobalChat processes"
  value       = local.deployment_processes
}

output "s3_vpc_endpoint_id" {
  value = aws_vpc_endpoint.s3.id
}
