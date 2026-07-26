output "api_service_name" {
  description = "Name of the API ECS service"
  value       = aws_ecs_service.api.name
}

output "frontend_service_name" {
  description = "Name of the frontend ECS service"
  value       = aws_ecs_service.frontend.name
}

output "worker_service_name" {
  description = "Name of the worker ECS service"
  value       = aws_ecs_service.worker.name
}

output "beat_service_name" {
  description = "Name of the beat ECS service"
  value       = aws_ecs_service.beat.name
}

output "migrate_task_definition_arn" {
  description = "ARN of the migration task definition (run as one-shot ECS task)"
  value       = aws_ecs_task_definition.migrate.arn
}

output "task_role_arn" {
  description = "ARN of the ECS task IAM role"
  value       = aws_iam_role.task.arn
}

output "execution_role_arn" {
  description = "ARN of the ECS task execution IAM role"
  value       = aws_iam_role.execution.arn
}
