#!/bin/bash

# Script to automate downloading the LANL Unified Host and Network Dataset
# specifically for day 02 and day 04, to keep the dataset size manageable.

set -e

# Create data directories if they don't exist
mkdir -p data/HostEvent
mkdir -p data/NetFlow

echo "Downloading HostEvent data for Day 02..."
curl -o data/HostEvent/wls_day-02.bz2 -L https://csr.lanl.gov/data/2017/wls_day-02.bz2

echo "Downloading HostEvent data for Day 04..."
curl -o data/HostEvent/wls_day-04.bz2 -L https://csr.lanl.gov/data/2017/wls_day-04.bz2

echo "Downloading NetFlow data for Day 02..."
curl -o data/NetFlow/netflow_day-02.bz2 -L https://csr.lanl.gov/data/2017/netflow_day-02.bz2

echo "Downloading NetFlow data for Day 04..."
curl -o data/NetFlow/netflow_day-04.bz2 -L https://csr.lanl.gov/data/2017/netflow_day-04.bz2

echo "Download complete! Files are saved in data/HostEvent/ and data/NetFlow/"
