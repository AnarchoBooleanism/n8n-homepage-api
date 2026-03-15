#!/bin/bash

fastapi run --forwarded-allow-ips="${FORWARDED_ALLOW_IPS}" --root-path "${ROOT_PATH_PREFIX}" --port "${FASTAPI_PORT}" /app/main.py