#!/bin/bash

sudo mkdir -p /etc/bgrp
sudo cp ./src/bgrp.py /usr/bin/bgrp.py
sudo cp ./src/config.py /etc/bgrp/config.py
sudo cp ./src/bgrp.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl status bgrp.service
