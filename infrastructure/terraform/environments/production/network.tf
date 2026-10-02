data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)
}

resource "aws_vpc" "globalchat" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "globalchat-production-vpc"
  }
}

resource "aws_subnet" "public" {
  for_each = {
    a = { cidr = "10.42.0.0/24", az = local.availability_zones[0] }
    b = { cidr = "10.42.1.0/24", az = local.availability_zones[1] }
  }

  vpc_id                  = aws_vpc.globalchat.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = true

  tags = {
    Name = "globalchat-production-public-${each.key}"
    Tier = "public"
  }
}

resource "aws_subnet" "private_app" {
  for_each = {
    a = { cidr = "10.42.10.0/24", az = local.availability_zones[0] }
    b = { cidr = "10.42.11.0/24", az = local.availability_zones[1] }
  }

  vpc_id                  = aws_vpc.globalchat.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = false

  tags = {
    Name = "globalchat-production-app-${each.key}"
    Tier = "application"
  }
}

resource "aws_subnet" "private_data" {
  for_each = {
    a = { cidr = "10.42.20.0/24", az = local.availability_zones[0] }
    b = { cidr = "10.42.21.0/24", az = local.availability_zones[1] }
  }

  vpc_id                  = aws_vpc.globalchat.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = false

  tags = {
    Name = "globalchat-production-data-${each.key}"
    Tier = "data"
  }
}

resource "aws_internet_gateway" "globalchat" {
  vpc_id = aws_vpc.globalchat.id

  tags = {
    Name = "globalchat-production-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.globalchat.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.globalchat.id
  }

  tags = {
    Name = "globalchat-production-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "globalchat-production-nat-eip"
  }
}

resource "aws_nat_gateway" "globalchat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public["a"].id

  depends_on = [aws_internet_gateway.globalchat]

  tags = {
    Name = "globalchat-production-nat-a"
  }
}

resource "aws_route_table" "private_app" {
  vpc_id = aws_vpc.globalchat.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.globalchat.id
  }

  tags = {
    Name = "globalchat-production-app-rt"
  }
}

resource "aws_route_table_association" "private_app" {
  for_each = aws_subnet.private_app

  subnet_id      = each.value.id
  route_table_id = aws_route_table.private_app.id
}

resource "aws_route_table" "private_data" {
  vpc_id = aws_vpc.globalchat.id

  tags = {
    Name = "globalchat-production-data-rt"
  }
}

resource "aws_route_table_association" "private_data" {
  for_each = aws_subnet.private_data

  subnet_id      = each.value.id
  route_table_id = aws_route_table.private_data.id
}

resource "aws_security_group" "alb" {
  name        = "globalchat-production-alb-sg"
  description = "Base security group for the future GlobalChat ALB"
  vpc_id      = aws_vpc.globalchat.id

  tags = {
    Name = "globalchat-production-alb-sg"
  }
}

resource "aws_security_group" "ecs" {
  name        = "globalchat-production-ecs-sg"
  description = "Base security group for future GlobalChat ECS tasks"
  vpc_id      = aws_vpc.globalchat.id

  tags = {
    Name = "globalchat-production-ecs-sg"
  }
}

resource "aws_security_group" "rds" {
  name        = "globalchat-production-rds-sg"
  description = "Base security group for future GlobalChat RDS resources"
  vpc_id      = aws_vpc.globalchat.id

  tags = {
    Name = "globalchat-production-rds-sg"
  }
}

resource "aws_security_group" "redis" {
  name        = "globalchat-production-redis-sg"
  description = "Base security group for future GlobalChat Redis resources"
  vpc_id      = aws_vpc.globalchat.id

  tags = {
    Name = "globalchat-production-redis-sg"
  }
}

resource "aws_security_group" "rabbitmq" {
  name        = "globalchat-production-rabbitmq-sg"
  description = "Base security group for future GlobalChat RabbitMQ resources"
  vpc_id      = aws_vpc.globalchat.id

  tags = {
    Name = "globalchat-production-rabbitmq-sg"
  }
}
