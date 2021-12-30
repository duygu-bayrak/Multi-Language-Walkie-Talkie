#!/bin/bash
python3 -u ./Multi-Language-Walkie-Talkie/server.py 10319 10319 2>&1 | tee log_10319.txt &
python3 -u ./Multi-Language-Walkie-Talkie/server.py 10320 10320 2>&1 | tee log_10320.txt &
ps -ef | grep python3
