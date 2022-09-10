variable "project_id" {
  defadefault = "glass-haven-360720"
}

variable "region" {
  default = "eu-west2"
}

variable "zone" {
  default = "eu-west2-a"
}

variable "service_account_id" {
  default = "my-service-account"
}

variable "service_account_email" {
  default = "${service_account_id}@glass-haven-360720.iam.gserviceaccount.com"
}

