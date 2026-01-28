#!/bin/bash

set -e

# sobe a interface
ip link set eth0 up

# tenta DHCP (NAT do GNS3)
dhclient eth0

# inicia rsyslog em foreground
exec rsyslogd -n
