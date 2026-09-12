#!/bin/bash
set -e
set -o pipefail

echo "======================================"
echo "SGC AI Agent: EC2 Deployment Script"
echo "======================================"

# Ensure we are in the project root
cd "$(dirname "$0")/.."

BRANCH=${1:-main}
AWS_SECRET_NAME=${2:-sgc_ai_kr}
AWS_REGION="ap-south-1"
echo "[1/5] Pulling latest code from GitHub ($BRANCH branch)..."
git reset --hard HEAD
git pull origin $BRANCH

echo "[2/5] Fetching secrets from AWS Secrets Manager..."
if [ -n "$AWS_SECRET_NAME" ]; then
    echo "Fetching secret: $AWS_SECRET_NAME in region $AWS_REGION"
    # Ensure AWS CLI is configured via IAM Role, and jq is installed
    aws secretsmanager get-secret-value --region "$AWS_REGION" --secret-id "$AWS_SECRET_NAME" --query SecretString --output text | jq -r 'to_entries|map("\(.key)=\(.value|tostring)")|.[]' > .env
    echo ".env file generated from Secrets Manager. Keys found:"
    awk -F= '{print $1}' .env || true
else
    echo "Warning: AWS_SECRET_NAME not provided. Skipping secret fetch."
fi

echo "[3/5] Starting Docker containers with GPU support..."
# Note: Ensure NVIDIA Container Toolkit is installed on your g6.2xlarge instance.
docker compose -f infra/docker-compose.prod.yml up -d --build

echo "[3/5] Waiting for services to be healthy..."
sleep 15 # Wait a bit for postgres to initialize before migrations

echo "[4/5] Running database migrations..."
docker compose -f infra/docker-compose.prod.yml exec -T agent-api uv run --package sgc-db alembic -c packages/db/alembic.ini upgrade head

echo "[5/5] Downloading llama3.1:8b model into Ollama container..."
# This may take a few minutes depending on network speed
docker compose -f infra/docker-compose.prod.yml exec -T ollama ollama run llama3.1:8b "Hello"

echo "======================================"
echo "Deployment Complete!"
echo "API is accessible at http://<EC2-PUBLIC-IP>:8000"
echo "Make sure Port 8000 is open in your EC2 Security Group."
echo "======================================"
