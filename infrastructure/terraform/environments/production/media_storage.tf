locals {
  media_bucket_name = "globalchat-production-media-${local.account_id}-ap-south-1"

  media_validation_script = <<-PYTHON
    import os
    import urllib.error
    import urllib.request
    import uuid
    import xml.etree.ElementTree as ET

    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError


    region = os.environ["AWS_REGION"]
    bucket = os.environ["MEDIA_S3_BUCKET"]
    state_bucket = os.environ["TERRAFORM_STATE_BUCKET"]
    external_bucket = os.environ["EXTERNAL_BUCKET"]
    key = f"validation/{uuid.uuid4().hex}/object.txt"
    payload = b"globalchat-media-validation"
    s3 = boto3.client(
        "s3",
        region_name=region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )
    sts = boto3.client("sts", region_name=region)


    def expect_head_denied(name):
        try:
            s3.head_bucket(Bucket=name)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") not in {"403", "AccessDenied"}:
                raise
        else:
            raise RuntimeError(f"unexpected access to protected bucket: {name}")


    def s3_error_code(content):
        try:
            return ET.fromstring(content).findtext("Code") or "Unknown"
        except ET.ParseError:
            return "Unparseable"


    def request(url, method, body=None, headers=None):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, data=body, method=method, headers=headers or {}),
                timeout=30,
            ) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()


    def delete_validation_versions():
        response = s3.list_object_versions(Bucket=bucket, Prefix=key)
        for collection in ("Versions", "DeleteMarkers"):
            for item in response.get(collection, []):
                if item["Key"] == key:
                    s3.delete_object(
                        Bucket=bucket,
                        Key=key,
                        VersionId=item["VersionId"],
                    )

        remaining = s3.list_object_versions(Bucket=bucket, Prefix=key)
        if any(
            item["Key"] == key
            for collection in ("Versions", "DeleteMarkers")
            for item in remaining.get(collection, [])
        ):
            raise RuntimeError("temporary object versions were not deleted")


    identity = sts.get_caller_identity()["Arn"]
    if ":assumed-role/globalchat-production-media-task/" not in identity:
        raise RuntimeError("validation is not using the Media task role")

    try:
        s3.put_object(Bucket=bucket, Key=key, Body=payload, ContentType="text/plain")
        s3.delete_object(Bucket=bucket, Key=key)
        put_url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": "text/plain"},
            ExpiresIn=300,
            HttpMethod="PUT",
        )
        put_status, put_body = request(
            put_url, "PUT", payload, {"Content-Type": "text/plain"}
        )
        if put_status != 200:
            raise RuntimeError(
                f"presigned upload failed with HTTP {put_status} "
                f"and S3 code {s3_error_code(put_body)}"
            )
        head = s3.head_object(Bucket=bucket, Key=key)
        if head["ContentLength"] != len(payload) or head.get("ContentType") != "text/plain":
            raise RuntimeError("HeadObject verification failed")
        get_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=300,
            HttpMethod="GET",
        )
        get_status, get_body = request(get_url, "GET")
        if get_status != 200:
            raise RuntimeError(
                f"presigned download failed with HTTP {get_status} "
                f"and S3 code {s3_error_code(get_body)}"
            )
        if get_body != payload:
            raise RuntimeError("presigned download verification failed")
        expect_head_denied(external_bucket)
        expect_head_denied(state_bucket)
        try:
            s3.list_buckets()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") not in {"403", "AccessDenied"}:
                raise
        else:
            raise RuntimeError("unexpected permission to enumerate unrelated buckets")
    finally:
        s3.delete_object(Bucket=bucket, Key=key)
        delete_validation_versions()

    try:
        s3.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in {"404", "NoSuchKey", "NotFound"}:
            raise
    else:
        raise RuntimeError("temporary object was not deleted")

    print("Media task-role identity, presigned PUT/GET, HEAD, delete, cleanup, and negative IAM validation completed.")
  PYTHON
}

resource "aws_s3_bucket" "media" {
  bucket        = local.media_bucket_name
  force_destroy = false

  tags = {
    Name    = "globalchat-production-media"
    Service = "media"
  }
}

resource "aws_s3_bucket_public_access_block" "media" {
  bucket = aws_s3_bucket.media.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket_versioning" "media" {
  bucket = aws_s3_bucket.media.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    expiration {
      expired_object_delete_marker = true
    }
  }

  depends_on = [aws_s3_bucket_versioning.media]
}

resource "aws_s3_bucket_cors_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  cors_rule {
    allowed_headers = ["Content-Type", "x-amz-checksum-sha256"]
    allowed_methods = ["GET", "HEAD", "PUT"]
    allowed_origins = [
      "https://michat.in",
      "https://app.michat.in",
      "https://admin.michat.in",
    ]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

data "aws_iam_policy_document" "media_bucket" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.media.arn,
      "${aws_s3_bucket.media.arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "media" {
  bucket = aws_s3_bucket.media.id
  policy = data.aws_iam_policy_document.media_bucket.json

  depends_on = [aws_s3_bucket_public_access_block.media]
}

data "aws_iam_policy_document" "media_task_assume_role" {
  statement {
    sid     = "EcsTasksAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "media_task" {
  name                 = "globalchat-production-media-task"
  description          = "GlobalChat production Media application task role"
  assume_role_policy   = data.aws_iam_policy_document.media_task_assume_role.json
  max_session_duration = 3600

  tags = {
    Name    = "globalchat-production-media-task"
    Service = "media"
  }
}

data "aws_iam_policy_document" "media_task" {
  statement {
    sid     = "DenyProtectedBuckets"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      "arn:aws:s3:::devisha-properties-bucket",
      "arn:aws:s3:::devisha-properties-bucket/*",
      "arn:aws:s3:::${local.state_bucket_name}",
      "arn:aws:s3:::${local.state_bucket_name}/*",
    ]
  }

  statement {
    sid       = "MediaBucketReadiness"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.media.arn]
  }

  statement {
    sid       = "ValidationVersionListing"
    effect    = "Allow"
    actions   = ["s3:ListBucketVersions"]
    resources = [aws_s3_bucket.media.arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["validation/*"]
    }
  }

  statement {
    sid    = "MediaObjectOperations"
    effect = "Allow"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:ListMultipartUploadParts",
      "s3:PutObject",
    ]
    resources = ["${aws_s3_bucket.media.arn}/organizations/*", "${aws_s3_bucket.media.arn}/validation/*"]
  }

  statement {
    sid       = "ValidationObjectVersionCleanup"
    effect    = "Allow"
    actions   = ["s3:DeleteObjectVersion"]
    resources = ["${aws_s3_bucket.media.arn}/validation/*"]
  }
}

resource "aws_iam_policy" "media_task" {
  name        = "globalchat-production-media-task"
  description = "Least-privilege access to the GlobalChat production media bucket"
  policy      = data.aws_iam_policy_document.media_task.json

  tags = {
    Name    = "globalchat-production-media-task"
    Service = "media"
  }
}

resource "aws_iam_role_policy_attachment" "media_task" {
  role       = aws_iam_role.media_task.name
  policy_arn = aws_iam_policy.media_task.arn
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.globalchat.id
  service_name      = "com.amazonaws.ap-south-1.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private_app.id]

  tags = {
    Name = "globalchat-production-s3"
  }
}

resource "aws_cloudwatch_log_group" "media_validation" {
  name              = "/globalchat/production/media-validation"
  retention_in_days = 7

  tags = {
    Name    = "globalchat-production-media-validation-logs"
    Service = "media"
  }
}

resource "aws_ecs_task_definition" "media_validation" {
  family                   = "globalchat-production-media-validation"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.media_task.arn

  container_definitions = jsonencode([
    {
      name       = "media-validation"
      image      = "public.ecr.aws/docker/library/python:3.12-slim"
      essential  = true
      entryPoint = ["/bin/sh", "-c"]
      command = [
        "pip install --quiet 'boto3>=1.35,<2' && echo \"$VALIDATION_SCRIPT_B64\" | base64 -d > /tmp/validate.py && python /tmp/validate.py",
      ]
      environment = [
        {
          name  = "AWS_REGION"
          value = "ap-south-1"
        },
        {
          name  = "MEDIA_S3_BUCKET"
          value = aws_s3_bucket.media.id
        },
        {
          name  = "TERRAFORM_STATE_BUCKET"
          value = local.state_bucket_name
        },
        {
          name  = "EXTERNAL_BUCKET"
          value = "devisha-properties-bucket"
        },
        {
          name  = "VALIDATION_SCRIPT_B64"
          value = base64encode(local.media_validation_script)
        },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.media_validation.name
          "awslogs-region"        = "ap-south-1"
          "awslogs-stream-prefix" = "validation"
        }
      }
    },
  ])

  depends_on = [
    aws_iam_role_policy_attachment.media_task,
    aws_s3_bucket_policy.media,
    aws_s3_bucket_cors_configuration.media,
    aws_s3_bucket_lifecycle_configuration.media,
  ]

  tags = {
    Name    = "globalchat-production-media-validation"
    Service = "media"
  }
}

data "aws_iam_policy_document" "github_media_foundation" {
  statement {
    sid = "ManageGlobalChatMediaBucket"
    actions = [
      "s3:CreateBucket",
      "s3:DeleteBucket",
      "s3:GetBucketAcl",
      "s3:GetBucketCORS",
      "s3:GetBucketLocation",
      "s3:GetBucketPolicy",
      "s3:GetBucketPolicyStatus",
      "s3:GetBucketPublicAccessBlock",
      "s3:GetBucketTagging",
      "s3:GetBucketVersioning",
      "s3:GetEncryptionConfiguration",
      "s3:GetLifecycleConfiguration",
      "s3:GetBucketOwnershipControls",
      "s3:ListBucket",
      "s3:PutBucketCORS",
      "s3:PutBucketPolicy",
      "s3:PutBucketPublicAccessBlock",
      "s3:PutBucketTagging",
      "s3:PutBucketVersioning",
      "s3:PutEncryptionConfiguration",
      "s3:PutLifecycleConfiguration",
      "s3:PutBucketOwnershipControls",
    ]
    resources = ["arn:aws:s3:::${local.media_bucket_name}"]
  }

  statement {
    sid = "ManageGlobalChatMediaTaskRole"
    actions = [
      "iam:AttachRolePolicy",
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:DetachRolePolicy",
      "iam:GetRole",
      "iam:ListAttachedRolePolicies",
      "iam:ListInstanceProfilesForRole",
      "iam:ListRolePolicies",
      "iam:ListRoleTags",
      "iam:PassRole",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:UpdateRoleDescription",
    ]
    resources = ["arn:aws:iam::${local.account_id}:role/globalchat-production-media-task"]
  }

  statement {
    sid = "ManageGlobalChatMediaPolicies"
    actions = [
      "iam:CreatePolicy",
      "iam:CreatePolicyVersion",
      "iam:DeletePolicy",
      "iam:DeletePolicyVersion",
      "iam:GetPolicy",
      "iam:GetPolicyVersion",
      "iam:ListEntitiesForPolicy",
      "iam:ListPolicyTags",
      "iam:ListPolicyVersions",
      "iam:TagPolicy",
      "iam:UntagPolicy",
    ]
    resources = [
      "arn:aws:iam::${local.account_id}:policy/globalchat-production-media-task",
      "arn:aws:iam::${local.account_id}:policy/globalchat-production-media-foundation",
    ]
  }

  statement {
    sid = "ManageGlobalChatS3Endpoint"
    actions = [
      "ec2:CreateTags",
      "ec2:CreateVpcEndpoint",
      "ec2:DeleteVpcEndpoints",
      "ec2:DescribeRouteTables",
      "ec2:DescribeVpcAttribute",
      "ec2:DescribeVpcEndpoints",
      "ec2:ModifyVpcEndpoint",
    ]
    resources = ["*"]
  }

  statement {
    sid = "ManageMediaValidationTaskDefinition"
    actions = [
      "ecs:DeregisterTaskDefinition",
      "ecs:DescribeTaskDefinition",
      "ecs:RegisterTaskDefinition",
      "ecs:TagResource",
      "ecs:UntagResource",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "github_media_foundation" {
  name        = "globalchat-production-media-foundation"
  description = "Least-privilege GitHub deployment permissions for GlobalChat media storage"
  policy      = data.aws_iam_policy_document.github_media_foundation.json

  tags = {
    Name = "globalchat-production-media-foundation"
  }
}

resource "aws_iam_role_policy_attachment" "github_media_foundation" {
  role       = aws_iam_role.github_deploy.name
  policy_arn = aws_iam_policy.github_media_foundation.arn
}
