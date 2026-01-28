FROM debian:bullseye

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    rsyslog \
    iproute2 \
    iputils-ping \
    net-tools \
    isc-dhcp-client \
    sudo \
    curl \
    procps \
    vim \
    ca-certificates \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
