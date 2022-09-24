#!/bin/bash

/usr/local/bin/entrypoint.py

tor --version

su torservice -c "tor -f /tor/torrc"
