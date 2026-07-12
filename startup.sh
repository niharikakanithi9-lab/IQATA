#!/bin/bash

echo "Starting IQATA Dashboard"

python -m streamlit run dashboard/app.py \
--server.port 8000 \
--server.address 0.0.0.0