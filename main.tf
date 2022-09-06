provider "google" {
  credentials = "${file("glass-haven-360720-428d8438af1c.json")}"
  project = "glass-haven-360720"
  region  = "eu-west2"
  zone    = "eu-west2-a"
}

