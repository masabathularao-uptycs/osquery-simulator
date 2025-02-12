#!/bin/bash

# Enable error handling
set -e

# Delete all files inside host_names/
rm -rf hostnames/*

# Delete all files starting with "osx"
rm -f osx_log*

echo "hostnames/* folder contents and osx_log/* files have been deleted."
