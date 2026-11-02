terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "pulse_net" {
  name = "pulse_net"
}

resource "docker_image" "pulse_api" {
  name = "pulse-api:0.1.0"
  build {
    context    = "."
    dockerfile = "Dockerfile"
  }
}

resource "docker_container" "api_1" {
  name  = "pulse-api-1"
  image = docker_image.pulse_api.image_id
  networks_advanced {
    name    = docker_network.pulse_net.name
    aliases = ["api"]
  }
  restart = "always"
  memory  = 536870912 # 512MB
}

resource "docker_container" "api_2" {
  name  = "pulse-api-2"
  image = docker_image.pulse_api.image_id
  networks_advanced {
    name    = docker_network.pulse_net.name
    aliases = ["api"]
  }
  restart = "always"
  memory  = 536870912 # 512MB
}

resource "docker_image" "nginx" {
  name = "nginx:alpine"
}

resource "docker_container" "proxy" {
  name  = "pulse-proxy"
  image = docker_image.nginx.image_id
  networks_advanced {
    name = docker_network.pulse_net.name
  }
  ports {
    internal = 80
    external = 8080
  }
  volumes {
    host_path      = "${abspath(path.module)}/nginx/nginx.conf"
    container_path = "/etc/nginx/nginx.conf"
    read_only      = true
  }
  restart    = "always"
  depends_on = [docker_container.api_1, docker_container.api_2]
}
