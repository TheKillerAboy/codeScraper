#!/bin/sh

rm -rf /venv
which python3.8
python3.8 -m venv venv
/home/kalilaptop/Documents/GitHub/codeScraper/venv/bin/python3.8 -m pip install --upgrade pip
/home/kalilaptop/Documents/GitHub/codeScraper/venv/bin/pip3 install -r requirements.txt