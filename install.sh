#!/bin/bash

echo "[*] Installing dependecies..."
if [[ -x "$(command -v apt)" ]]; then
	sudo apt update && sudo apt install tcpdump iproute2 -y
elif [[ -x "$(command -v yum)" ]]; then
	sudo yum update -y && sudo yum install tcpdump iproute2 -y
else
	echo "[X] Unsupported distribution or package manager not found."
	exit 1
fi

echo "[*] Copy script, config, service"
sudo mkdir -p /etc/bgrp
sudo cp ./src/bgrp.py /usr/bin/bgrp.py
sudo cp ./src/config.py /etc/bgrp/config.py
sudo cp ./src/bgrp.service /etc/systemd/system/

echo "[*] Reload systemd"
sudo systemctl daemon-reload
sudo systemctl status bgrp.service
