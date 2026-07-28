#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
npm run build:sdk
echo "SDK built at sdks/typescript/dist"
