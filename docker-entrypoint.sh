#!/bin/bash

fastapi run --forwarded-allow-ips="${FORWARDED_ALLOW_IPS}" --root-path "${ROOT_PATH_PREFIX}" --host "${FASTAPI_HOST}" --port "${FASTAPI_PORT}" /app/main.py