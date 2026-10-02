# GlobalChat Terraform

The `bootstrap` configuration creates the dedicated, protected S3 bucket used for Terraform state. Its state remains local and must be retained securely because Terraform cannot use the bucket before it exists.

The `environments/production` configuration uses the remote S3 backend with native lockfiles. It creates the repository-restricted GitHub Actions OIDC provider and the foundation deployment role.

All resources use the `GlobalChat`, `production`, and `Terraform` ownership tags. Existing account resources are not imported or managed here.
