#!/bin/sh
set -e
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} 