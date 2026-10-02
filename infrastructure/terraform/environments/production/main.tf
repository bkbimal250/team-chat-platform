locals {
  account_id           = "167667034490"
  github_repository    = "bkbimal250/team-chat-platform"
  deployment_branch    = "main"
  state_bucket_name    = "globalchat-production-terraform-state-167667034490-ap-south-1"
  deployment_role_name = "globalchat-production-github-deploy"
}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  tags = {
    Name = "globalchat-production-github-oidc"
  }
}

data "aws_iam_policy_document" "github_assume_role" {
  statement {
    sid     = "GitHubActionsMainBranch"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${local.github_repository}:ref:refs/heads/${local.deployment_branch}"]
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  name                 = local.deployment_role_name
  description          = "GlobalChat production deployment role for GitHub Actions"
  assume_role_policy   = data.aws_iam_policy_document.github_assume_role.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "github_foundation" {
  statement {
    sid = "ListTerraformState"
    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucket",
    ]
    resources = ["arn:aws:s3:::${local.state_bucket_name}"]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["production/*"]
    }
  }

  statement {
    sid = "ManageTerraformState"
    actions = [
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = ["arn:aws:s3:::${local.state_bucket_name}/production/*"]
  }
}

resource "aws_iam_role_policy" "github_foundation" {
  name   = "globalchat-production-terraform-state"
  role   = aws_iam_role.github_deploy.id
  policy = data.aws_iam_policy_document.github_foundation.json
}
