resource "aws_route53_zone" "michat" {
  name    = "michat.in"
  comment = "GlobalChat production public DNS zone"

  tags = {
    Name = "globalchat-production-public-zone"
  }
}
