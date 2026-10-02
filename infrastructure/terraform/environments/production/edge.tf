resource "aws_acm_certificate" "michat" {
  domain_name               = "michat.in"
  subject_alternative_names = ["*.michat.in"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "globalchat-production-michat-certificate"
  }
}

locals {
  michat_apex_validation = one([
    for option in aws_acm_certificate.michat.domain_validation_options : option
    if option.domain_name == "michat.in"
  ])
}

resource "aws_route53_record" "michat_certificate_validation" {
  zone_id = aws_route53_zone.michat.zone_id
  name    = local.michat_apex_validation.resource_record_name
  type    = local.michat_apex_validation.resource_record_type
  records = [local.michat_apex_validation.resource_record_value]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "michat" {
  certificate_arn         = aws_acm_certificate.michat.arn
  validation_record_fqdns = [aws_route53_record.michat_certificate_validation.fqdn]

  timeouts {
    create = "45m"
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  description       = "Public HTTPS ingress"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  ip_protocol       = "tcp"
  to_port           = 443
}

resource "aws_vpc_security_group_ingress_rule" "alb_http_redirect" {
  security_group_id = aws_security_group.alb.id
  description       = "Public HTTP ingress for HTTPS redirect"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "alb_to_api" {
  security_group_id            = aws_security_group.alb.id
  description                  = "ALB to API targets"
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 8000
  ip_protocol                  = "tcp"
  to_port                      = 8000
}

resource "aws_vpc_security_group_egress_rule" "alb_to_realtime" {
  security_group_id            = aws_security_group.alb.id
  description                  = "ALB to realtime targets"
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 8007
  ip_protocol                  = "tcp"
  to_port                      = 8007
}

resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb_api" {
  security_group_id            = aws_security_group.ecs.id
  description                  = "API traffic from GlobalChat ALB"
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8000
  ip_protocol                  = "tcp"
  to_port                      = 8000
}

resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb_realtime" {
  security_group_id            = aws_security_group.ecs.id
  description                  = "Realtime traffic from GlobalChat ALB"
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8007
  ip_protocol                  = "tcp"
  to_port                      = 8007
}

resource "aws_lb" "globalchat" {
  name                       = "globalchat-production-alb"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb.id]
  subnets                    = [aws_subnet.public["a"].id, aws_subnet.public["b"].id]
  idle_timeout               = 300
  enable_deletion_protection = true

  tags = {
    Name = "globalchat-production-alb"
  }
}

resource "aws_lb_target_group" "api" {
  name        = "globalchat-production-api"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.globalchat.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health/ready"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = {
    Name = "globalchat-production-api"
  }
}

resource "aws_lb_target_group" "realtime" {
  name        = "globalchat-production-realtime"
  port        = 8007
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.globalchat.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health/ready"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = {
    Name = "globalchat-production-realtime"
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.globalchat.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = aws_acm_certificate_validation.michat.certificate_arn

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "application/json"
      message_body = "{\"detail\":\"Not Found\"}"
      status_code  = "404"
    }
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.globalchat.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    host_header {
      values = ["api.michat.in"]
    }
  }
}

resource "aws_lb_listener_rule" "realtime" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 110

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.realtime.arn
  }

  condition {
    host_header {
      values = ["ws.michat.in"]
    }
  }
}

resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.michat.zone_id
  name    = "api.michat.in"
  type    = "A"

  alias {
    name                   = aws_lb.globalchat.dns_name
    zone_id                = aws_lb.globalchat.zone_id
    evaluate_target_health = false
  }

  depends_on = [aws_lb_listener.https]
}

resource "aws_route53_record" "ws" {
  zone_id = aws_route53_zone.michat.zone_id
  name    = "ws.michat.in"
  type    = "A"

  alias {
    name                   = aws_lb.globalchat.dns_name
    zone_id                = aws_lb.globalchat.zone_id
    evaluate_target_health = false
  }

  depends_on = [aws_lb_listener.https]
}
