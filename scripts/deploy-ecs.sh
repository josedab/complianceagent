#!/usr/bin/env bash
set -euo pipefail

required_vars=(
  AWS_REGION
  CLUSTER
  DEPLOY_ENVIRONMENT
  GHCR_REPOSITORY
  GHCR_USER
  GHCR_TOKEN
  IMAGE_TAG
  PRIVATE_SUBNETS
  ECS_SECURITY_GROUP
)

for name in "${required_vars[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
done

account_id=$(aws sts get-caller-identity --query Account --output text)
ecr_registry="${account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com"

printf '%s' "$GHCR_TOKEN" | docker login ghcr.io --username "$GHCR_USER" --password-stdin
aws ecr get-login-password --region "$AWS_REGION" |
  docker login --username AWS --password-stdin "$ecr_registry"

promote_image() {
  local source_image=$1
  local repository=$2
  local target_image="${ecr_registry}/${repository}:${IMAGE_TAG}"

  if ! aws ecr describe-images \
    --repository-name "$repository" \
    --image-ids "imageTag=${IMAGE_TAG}" >/dev/null 2>&1; then
    docker pull "$source_image" >&2
    docker tag "$source_image" "$target_image"
    docker push "$target_image" >&2
  fi
  printf '%s\n' "$target_image"
}

api_image=$(promote_image "ghcr.io/${GHCR_REPOSITORY}-api:${IMAGE_TAG}" "complianceagent/backend")
frontend_image=$(promote_image "ghcr.io/${GHCR_REPOSITORY}-frontend:${IMAGE_TAG}" "complianceagent/frontend")
crawler_image=$(promote_image "ghcr.io/${GHCR_REPOSITORY}-crawler:${IMAGE_TAG}" "complianceagent/crawler")

register_task_definition() {
  local task_definition=$1
  local container_name=$2
  local image=$3
  local source_json target_json

  source_json=$(mktemp)
  target_json=$(mktemp)
  aws ecs describe-task-definition \
    --task-definition "$task_definition" \
    --query taskDefinition >"$source_json"
  jq --arg container "$container_name" --arg image "$image" '
    .containerDefinitions |= map(
      if .name == $container then .image = $image else . end
    )
    | del(
        .taskDefinitionArn,
        .revision,
        .status,
        .requiresAttributes,
        .compatibilities,
        .registeredAt,
        .registeredBy
      )
  ' "$source_json" >"$target_json"
  aws ecs register-task-definition \
    --cli-input-json "file://${target_json}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text
  rm -f "$source_json" "$target_json"
}

current_service_task() {
  local service=$1
  aws ecs describe-services \
    --cluster "$CLUSTER" \
    --services "$service" \
    --query 'services[0].taskDefinition' \
    --output text
}

api_service="complianceagent-api-${DEPLOY_ENVIRONMENT}"
frontend_service="complianceagent-frontend-${DEPLOY_ENVIRONMENT}"
worker_service="complianceagent-worker-${DEPLOY_ENVIRONMENT}"
beat_service="complianceagent-beat-${DEPLOY_ENVIRONMENT}"

api_task=$(register_task_definition "$(current_service_task "$api_service")" api "$api_image")
frontend_task=$(register_task_definition "$(current_service_task "$frontend_service")" frontend "$frontend_image")
worker_task=$(register_task_definition "$(current_service_task "$worker_service")" worker "$crawler_image")
beat_task=$(register_task_definition "$(current_service_task "$beat_service")" beat "$api_image")
migration_task=$(register_task_definition "complianceagent-migrate-${DEPLOY_ENVIRONMENT}" migrate "$api_image")

task_arn=$(aws ecs run-task \
  --cluster "$CLUSTER" \
  --task-definition "$migration_task" \
  --launch-type FARGATE \
  --network-configuration \
    "awsvpcConfiguration={subnets=[${PRIVATE_SUBNETS}],securityGroups=[${ECS_SECURITY_GROUP}],assignPublicIp=DISABLED}" \
  --query 'tasks[0].taskArn' \
  --output text)
aws ecs wait tasks-stopped --cluster "$CLUSTER" --tasks "$task_arn"
migration_exit=$(aws ecs describe-tasks \
  --cluster "$CLUSTER" \
  --tasks "$task_arn" \
  --query 'tasks[0].containers[0].exitCode' \
  --output text)
if [[ "$migration_exit" != "0" ]]; then
  echo "Migration failed with exit code ${migration_exit}" >&2
  exit 1
fi

aws ecs update-service --cluster "$CLUSTER" --service "$api_service" --task-definition "$api_task"
aws ecs update-service --cluster "$CLUSTER" --service "$frontend_service" --task-definition "$frontend_task"
aws ecs update-service --cluster "$CLUSTER" --service "$worker_service" --task-definition "$worker_task"
aws ecs update-service --cluster "$CLUSTER" --service "$beat_service" --task-definition "$beat_task"

aws ecs wait services-stable \
  --cluster "$CLUSTER" \
  --services "$api_service" "$frontend_service" "$worker_service" "$beat_service"
