terraform {
  backend "gcs" {
    bucket = "qwiklabs-gcp-04-27cfc397f163-terraform-state"
    prefix = "agentic-era-hack/dev"
  }
}
