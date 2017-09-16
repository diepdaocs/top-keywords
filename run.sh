#!/bin/bash
# Kill all process running on port
PORT=7777
fuser -k -n tcp ${PORT}

# Config environment
export PYTHONPATH=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
ENV=${PYTHONPATH}/env
HOST=0.0.0.0

# Start app
${ENV}/bin/python ${ENV}/bin/gunicorn -k tornado -w 2 -b ${HOST}:${PORT} relevant_keywords.main:app --max-requests 10000 --timeout 240
