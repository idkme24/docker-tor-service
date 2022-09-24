# docker-tor-service
A dockerized Tor service container

## Tor


## How to build the tor-service image
Run the _build\_tor-service\_image.sh_ to download the Tor source, compile it, and build a Docker image with the Tor executable. 
`bash build_tor-service_image.sh`

## How to use the tor-service image
Below are examples

```
---
version: "3"

services:
  ## example Tor proxy service
  tor-proxy:
    container_name: tor-proxy
    image: tor-service
    environment:
      ROLE: proxy
      PROXY_PORT: 9050
      PROXY_ADDRESS: 0.0.0.0
      PROXY_ACCEPT: 10.1.0.0/24
    volumes:
      - ./tor-proxy:/tor
    ports:
      - "9050:9050/tcp"
    restart: unless-stopped

  ## example Tor Onion/hidden service
  tor-service:
    container_name: tor-service
    image: tor-service
    environment:
      ROLE: service
      ONIONSERVICE_NAME: mywebservice
      ONIONSERVICE_PORT: 80
      ONIONSERVICE_HOST: clean-net-service-host-ip-here:80
      ONIONSERVICE_DIR: /tor/mywebservice
    volumes:
      - ./tor-service:/tor
    restart: unless-stopped

  ## example Tor control service
  tor-control:
    container_name: tor-control
    image: tor-service
    environment:
      ROLE: control
      CONTROL_PORT: 9051
      CONTROL_PASSWORD: 'changeme'
    volumes:
      - ./tor-control:/tor
    ports:
      - "9051:9051/tcp"
    restart: unless-stopped
```

## Docker Environment Variables
The entrypoint.py script accepts the following environment variables
```
   PUID                    uid of user
   PGID                    gid of user
   ROLE                    function of tor service 'service,relay,proxy'
   YAML_CFG                use torsrv.yml configuration file
   ONIONSERVICE_NAME       name of hiddenservice
   ONIONSERVICE_DIR        hiddenservice directory
   ONIONSERVICE_PORT       hiddenservice virtual port
   ONIONSERVICE_HOST       hiddenservice IP:PORT of service
   PROXY_PORT              proxy service port
   PROXY_ADDRESS           bind proxy service to address
   PROXY_ACCEPT            subnets which to accept SOCKS connections
   PROXY_REJECT            subnets which NOT to accept SOCKS connections
   CONTROL_PORT             
   CONTROL_PASSWORD         
   CONTROL_COOKIE           
   CFG_OVERWRITE           overwrite old cfg
   CFG_PATH                path to cfg in container
   BASE_DIR                base path for tor config/services
```

## Reference Material

