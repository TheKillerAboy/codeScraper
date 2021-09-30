#!/bin/sh

sudo rm -rf /lib/codeScraper
sudo cp -rf /home/kalilaptop/Documents/GitHub/codeScraper/dist/codeScraperLinux /lib/codeScraper

sudo rm /usr/bin/codeScraper
sudo ln -s /lib/codeScraper/codeScraper /usr/bin/codeScraper

if [ ! -f /etc/codeScraper.conf ]; then
    sudo cp /lib/codeScraper/config.yaml /etc/codeScraper.conf
fi