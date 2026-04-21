"""clean-agents export — generate deployment-ready infrastructure code."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from clean_agents.core.blueprint import Blueprint
from clean_agents.core.config import Config

console = Console()


def export_cmd(
    path: str = typer.Option("", "--path", "-p", help="Blueprint file path"),
    target: str = typer.Argument(
        ..., help="Export target: docker | k8s | terraform-aws | terraform-gcp | cloudformation"
    ),
    output: str = typer.Option("./deploy", "--output", "-o", help="Output directory"),
) -> None:
    """Export blueprint as deployment-ready infrastructure code.

    Generates infrastructure-as-code (IaC) files for deploying the agent system.
    Different from scaffold, which generates application code.
    """
    config = Config.discover()
    bp_path = Path(path) if path else config.blueprint_path()

    if not bp_path.exists():
        console.print("[red]Error:[/] No blueprint found. Run [bold]clean-agents design[/] first.")
        raise typer.Exit(1)

    blueprint = Blueprint.load(bp_path)
    out_dir = Path(output)

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Export[/] — Generating {target} infrastructure code",
        border_style="cyan",
    ))
    console.print()

    if target == "docker":
        _export_docker(blueprint, out_dir)
    elif target == "k8s":
        _export_k8s(blueprint, out_dir)
    elif target == "terraform-aws":
        _export_terraform_aws(blueprint, out_dir)
    elif target == "terraform-gcp":
        _export_terraform_gcp(blueprint, out_dir)
    elif target == "cloudformation":
        _export_cloudformation(blueprint, out_dir)
    else:
        console.print(f"[red]Error:[/] Unknown target {target}")
        raise typer.Exit(1)

    console.print(f"\n[green]✓[/] Infrastructure code exported to [bold]{out_dir}[/]")
    console.print()
    console.print("[dim]Next steps:[/]")
    if target == "docker":
        console.print(f"  cd {out_dir}")
        console.print("  docker-compose up -d")
        console.print("  # Check logs with: docker-compose logs -f")
    elif target == "k8s":
        console.print(f"  cd {out_dir}")
        console.print("  kubectl apply -k .")
        console.print("  kubectl get pods -n clean-agents")
    elif target.startswith("terraform"):
        console.print(f"  cd {out_dir}")
        console.print("  terraform init")
        console.print("  terraform plan")
        console.print("  terraform apply")
    elif target == "cloudformation":
        console.print(f"  cd {out_dir}")
        console.print("  aws cloudformation create-stack --stack-name clean-agents \\")
        console.print("    --template-body file://template.yaml")


def _export_docker(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate Docker and Docker Compose configuration."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate Dockerfile for each agent
    for agent in blueprint.agents:
        dockerfile_content = f"""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \\
    anthropic>=0.25 \\
    pydantic>=2.0 \\
    httpx \\
    pyyaml

# Copy agent code (to be filled by user)
COPY agents/{agent.name}.py /app/{agent.name}.py

# Environment variables (set at runtime)
ENV PYTHONUNBUFFERED=1
ENV AGENT_NAME={agent.name}
ENV MODEL={agent.model.primary}
ENV TOKEN_BUDGET={agent.token_budget}

EXPOSE 8000

# Default command
CMD ["python", "{agent.name}.py"]
"""
        agent_dir = out_dir / "agents"
        agent_dir.mkdir(exist_ok=True)
        (out_dir / f"Dockerfile.{agent.name}").write_text(dockerfile_content, encoding="utf-8")
        console.print(f"  [green]✓[/] Dockerfile.{agent.name}")

    # Generate docker-compose.yml
    services = {}

    # Add agents
    for agent in blueprint.agents:
        services[agent.name] = {
            "build": {
                "context": ".",
                "dockerfile": f"Dockerfile.{agent.name}",
            },
            "environment": [
                "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}",
                f"AGENT_NAME={agent.name}",
                f"MODEL={agent.model.primary}",
                f"TOKEN_BUDGET={agent.token_budget}",
            ],
            "depends_on": agent.dependencies if agent.dependencies else [],
            "networks": ["clean-agents"],
        }

    # Add Redis if message queue is configured
    if blueprint.infrastructure.message_queue:
        services["redis"] = {
            "image": "redis:7-alpine",
            "ports": ["6379:6379"],
            "networks": ["clean-agents"],
            "command": "redis-server --appendonly yes",
        }

    # Add PostgreSQL for state persistence
    services["postgres"] = {
        "image": "postgres:16-alpine",
        "environment": [
            "POSTGRES_USER=agents",
            "POSTGRES_PASSWORD=${DB_PASSWORD:-agents}",
            "POSTGRES_DB=agent_state",
        ],
        "ports": ["5432:5432"],
        "volumes": ["postgres_data:/var/lib/postgresql/data"],
        "networks": ["clean-agents"],
    }

    # Add vector DB if GraphRAG agents present
    if blueprint.has_graphrag():
        services["qdrant"] = {
            "image": "qdrant/qdrant:latest",
            "ports": ["6333:6333"],
            "volumes": ["qdrant_data:/qdrant/storage"],
            "networks": ["clean-agents"],
        }

    # Add observability if configured
    if blueprint.infrastructure.observability:
        if blueprint.infrastructure.observability == "langfuse":
            services["postgres"]["environment"].append("POSTGRES_HOST_AUTH_METHOD=trust")
            services["langfuse"] = {
                "image": "ghcr.io/langfuse/langfuse:latest",
                "depends_on": ["postgres"],
                "environment": [
                    "DATABASE_URL=postgresql://agents:agents@postgres:5432/langfuse",
                    "NEXTAUTH_SECRET=your-secret-here",
                    "NEXTAUTH_URL=http://localhost:3000",
                ],
                "ports": ["3000:3000"],
                "networks": ["clean-agents"],
            }

    compose_content = _generate_docker_compose_yaml(services)
    (out_dir / "docker-compose.yml").write_text(compose_content, encoding="utf-8")
    console.print("  [green]✓[/] docker-compose.yml")

    # Generate .env.example
    env_content = """# API Keys
ANTHROPIC_API_KEY=your-key-here

# Database
DB_PASSWORD=secure-password
POSTGRES_USER=agents
POSTGRES_PASSWORD=agents

# Observability
LANGFUSE_SECRET_KEY=your-key-here
LANGFUSE_PUBLIC_KEY=your-key-here

# Agent Configuration
AGENT_LOG_LEVEL=INFO
"""
    (out_dir / ".env.example").write_text(env_content, encoding="utf-8")
    console.print("  [green]✓[/] .env.example")

    # Generate Makefile
    makefile_content = f"""
.PHONY: up down logs build restart clean test

build:
\tdocker-compose build

up:
\tdocker-compose up -d

down:
\tdocker-compose down

logs:
\tdocker-compose logs -f

restart:
\tdocker-compose restart

clean:
\tdocker-compose down -v
\trm -rf postgres_data qdrant_data

test:
\tdocker-compose exec {blueprint.agents[0].name if blueprint.agents else 'agents'} pytest

ps:
\tdocker-compose ps
"""
    (out_dir / "Makefile").write_text(makefile_content, encoding="utf-8")
    console.print("  [green]✓[/] Makefile")


def _generate_docker_compose_yaml(services: dict) -> str:
    """Generate docker-compose.yml content from services dict."""
    lines = [
        "version: '3.8'",
        "",
        "services:",
    ]

    for service_name, service_config in services.items():
        lines.append(f"  {service_name}:")

        if "image" in service_config:
            lines.append(f"    image: {service_config['image']}")

        if "build" in service_config:
            build = service_config["build"]
            lines.append("    build:")
            lines.append(f"      context: {build.get('context', '.')}")
            lines.append(f"      dockerfile: {build.get('dockerfile', 'Dockerfile')}")

        if "environment" in service_config:
            lines.append("    environment:")
            for env in service_config["environment"]:
                lines.append(f"      - {env}")

        if "ports" in service_config:
            lines.append("    ports:")
            for port in service_config["ports"]:
                lines.append(f"      - {port}")

        if "depends_on" in service_config and service_config["depends_on"]:
            lines.append("    depends_on:")
            for dep in service_config["depends_on"]:
                lines.append(f"      - {dep}")

        if "volumes" in service_config:
            lines.append("    volumes:")
            for vol in service_config["volumes"]:
                lines.append(f"      - {vol}")

        if "networks" in service_config:
            lines.append("    networks:")
            for net in service_config["networks"]:
                lines.append(f"      - {net}")

        if "command" in service_config:
            lines.append(f"    command: {service_config['command']}")

        lines.append("")

    # Add networks section
    lines.extend([
        "networks:",
        "  clean-agents:",
        "    driver: bridge",
        "",
    ])

    # Add volumes section if needed
    has_volumes = any("volumes" in service for service in services.values())
    if has_volumes:
        lines.extend([
            "volumes:",
            "  postgres_data:",
        ])
        if any("qdrant" in service for service in services):
            lines.append("  qdrant_data:")

    return "\n".join(lines)


def _export_k8s(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate Kubernetes YAML manifests."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate namespace.yaml
    namespace_content = """apiVersion: v1
kind: Namespace
metadata:
  name: clean-agents
"""
    (out_dir / "namespace.yaml").write_text(namespace_content, encoding="utf-8")
    console.print("  [green]✓[/] namespace.yaml")

    # Generate ConfigMap for shared configuration
    configmap_content = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-config
  namespace: clean-agents
data:
  log_level: INFO
  pattern: {blueprint.pattern.value}
  system_type: {blueprint.system_type.value}
"""
    (out_dir / "configmap.yaml").write_text(configmap_content, encoding="utf-8")
    console.print("  [green]✓[/] configmap.yaml")

    # Generate Secret template
    secret_content = """apiVersion: v1
kind: Secret
metadata:
  name: agent-secrets
  namespace: clean-agents
type: Opaque
stringData:
  anthropic_api_key: "YOUR_ANTHROPIC_API_KEY"
  db_password: "secure-password"
  langfuse_secret_key: "YOUR_LANGFUSE_SECRET"
"""
    (out_dir / "secret.yaml").write_text(secret_content, encoding="utf-8")
    console.print("  [green]✓[/] secret.yaml")

    # Generate Deployment for each agent
    for agent in blueprint.agents:
        # Calculate resource limits based on token_budget
        memory_limit = f"{max(512, agent.token_budget // 2)}Mi"
        cpu_limit = f"{min(2, max(100, agent.token_budget // 1000))}m"

        deployment_content = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {agent.name}
  namespace: clean-agents
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {agent.name}
  template:
    metadata:
      labels:
        app: {agent.name}
        agent_type: {agent.agent_type}
    spec:
      containers:
      - name: {agent.name}
        image: clean-agents/{agent.name}:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: AGENT_NAME
          value: "{agent.name}"
        - name: MODEL
          value: "{agent.model.primary}"
        - name: TOKEN_BUDGET
          value: "{agent.token_budget}"
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: anthropic_api_key
        - name: DATABASE_URL
          value: "postgresql://agents:password@postgres:5432/agent_state"
        resources:
          requests:
            memory: {memory_limit}
            cpu: {cpu_limit}
          limits:
            memory: {memory_limit}
            cpu: {cpu_limit}
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
"""
        (out_dir / f"deployment-{agent.name}.yaml").write_text(deployment_content, encoding="utf-8")
        console.print(f"  [green]✓[/] deployment-{agent.name}.yaml")

        # Generate Service for each agent
        service_content = f"""apiVersion: v1
kind: Service
metadata:
  name: {agent.name}
  namespace: clean-agents
spec:
  selector:
    app: {agent.name}
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  type: ClusterIP
"""
        (out_dir / f"service-{agent.name}.yaml").write_text(service_content, encoding="utf-8")
        console.print(f"  [green]✓[/] service-{agent.name}.yaml")

    # Generate kustomization.yaml
    resource_files = [
        "namespace.yaml",
        "configmap.yaml",
        "secret.yaml",
    ]
    for agent in blueprint.agents:
        resource_files.extend([
            f"deployment-{agent.name}.yaml",
            f"service-{agent.name}.yaml",
        ])

    kustomization_content = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: clean-agents

resources:
"""
    for resource in resource_files:
        kustomization_content += f"  - {resource}\n"

    (out_dir / "kustomization.yaml").write_text(kustomization_content, encoding="utf-8")
    console.print("  [green]✓[/] kustomization.yaml")


def _export_terraform_aws(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate Terraform configuration for AWS ECS Fargate."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate main.tf
    main_tf_content = """terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "clean-agents-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/clean-agents"
  retention_in_days = 7
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "clean-agents-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.subnet_ids

  enable_deletion_protection = false
}

resource "aws_lb_target_group" "main" {
  name        = "clean-agents-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 30
    path                = "/"
    matcher             = "200"
  }
}

resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "clean-agents-alb-sg"
  description = "Security group for ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_tasks" {
  name        = "clean-agents-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ECS Task Definitions
"""

    # Generate task definitions for each agent
    for agent in blueprint.agents:
        main_tf_content += f"""
resource "aws_ecs_task_definition" "{agent.name}" {{
  family                   = "clean-agents-{agent.name}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([{{
    name      = "{agent.name}"
    image     = "${{var.ecr_registry}}/{agent.name}:latest"
    essential = true
    portMappings = [{{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }}]
    environment = [
      {{
        name  = "AGENT_NAME"
        value = "{agent.name}"
      }},
      {{
        name  = "MODEL"
        value = "{agent.model.primary}"
      }},
      {{
        name  = "TOKEN_BUDGET"
        value = "{agent.token_budget}"
      }}
    ]
    secrets = [
      {{
        name      = "ANTHROPIC_API_KEY"
        valueFrom = aws_secretsmanager_secret.anthropic_key.arn
      }}
    ]
    logConfiguration = {{
      logDriver = "awslogs"
      options = {{
        awslogs-group         = aws_cloudwatch_log_group.ecs.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }}
    }}
  }}])
}}

resource "aws_ecs_service" "{agent.name}" {{
  name            = "clean-agents-{agent.name}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.{agent.name}.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {{
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }}
  load_balancer {{
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "{agent.name}"
    container_port   = 8000
  }}
  depends_on = [aws_lb_listener.main]
}}
"""

    (out_dir / "main.tf").write_text(main_tf_content, encoding="utf-8")
    console.print("  [green]✓[/] main.tf")

    # Generate variables.tf
    variables_tf_content = """variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for ALB and ECS tasks"
  type        = list(string)
}

variable "ecr_registry" {
  description = "ECR registry URL (e.g., 123456789.dkr.ecr.us-east-1.amazonaws.com)"
  type        = string
}

variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  sensitive   = true
}
"""
    (out_dir / "variables.tf").write_text(variables_tf_content, encoding="utf-8")
    console.print("  [green]✓[/] variables.tf")

    # Generate outputs.tf
    outputs_tf_content = """output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.main.dns_name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}
"""
    (out_dir / "outputs.tf").write_text(outputs_tf_content, encoding="utf-8")
    console.print("  [green]✓[/] outputs.tf")

    # Generate iam.tf
    iam_tf_content = """# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "clean-agents-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "ecs-task-execution-secrets"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "kms:Decrypt"
      ]
      Resource = [
        aws_secretsmanager_secret.anthropic_key.arn,
        "${aws_secretsmanager_secret.anthropic_key.arn}:*"
      ]
    }]
  })
}

# IAM Role for ECS Task (application-level permissions)
resource "aws_iam_role" "ecs_task_role" {
  name = "clean-agents-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

# Secret for Anthropic API Key
resource "aws_secretsmanager_secret" "anthropic_key" {
  name                    = "clean-agents/anthropic-api-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "anthropic_key" {
  secret_id       = aws_secretsmanager_secret.anthropic_key.id
  secret_string   = var.anthropic_api_key
}
"""
    (out_dir / "iam.tf").write_text(iam_tf_content, encoding="utf-8")
    console.print("  [green]✓[/] iam.tf")

    # Generate terraform.tfvars.example
    tfvars_content = """aws_region = "us-east-1"
vpc_id = "vpc-xxxxxxxxx"
subnet_ids = ["subnet-xxxxxxxxx", "subnet-yyyyyyyyy"]
ecr_registry = "123456789.dkr.ecr.us-east-1.amazonaws.com"
anthropic_api_key = "sk-ant-xxxxx"
"""
    (out_dir / "terraform.tfvars.example").write_text(tfvars_content, encoding="utf-8")
    console.print("  [green]✓[/] terraform.tfvars.example")


def _export_terraform_gcp(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate Terraform configuration for Google Cloud Run."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate main.tf for GCP
    main_tf_content = """terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

# Cloud Run services for each agent
"""

    for agent in blueprint.agents:
        agent_name = agent.name
        agent_model = agent.model.primary
        agent_budget = agent.token_budget
        # Build terraform using string concatenation to avoid f-string brace issues
        service_block = (
            'resource "google_cloud_run_service" "' + agent_name + '" {\n'
            '  name     = "clean-agents-' + agent_name + '"\n'
            '  location = var.gcp_region\n'
            '\n  template {\n'
            '    spec {\n'
            '      service_account_email = google_service_account.agent.email\n'
            '      containers {\n'
            '        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project}/clean-agents/'
            + agent_name + ':latest"\n'
            '        ports {\n'
            '          container_port = 8000\n'
            '        }\n'
            '        env {\n'
            '          name  = "AGENT_NAME"\n'
            '          value = "' + agent_name + '"\n'
            '        }\n'
            '        env {\n'
            '          name  = "MODEL"\n'
            '          value = "' + agent_model + '"\n'
            '        }\n'
            '        env {\n'
            '          name  = "TOKEN_BUDGET"\n'
            '          value = "' + str(agent_budget) + '"\n'
            '        }\n'
            '        env {\n'
            '          name  = "ANTHROPIC_API_KEY"\n'
            '          value_from {\n'
            '            secret_key_ref {\n'
            '              name    = google_secret_manager_secret.anthropic_key.id\n'
            '              version = "latest"\n'
            '            }\n'
            '          }\n'
            '        }\n'
            '      }\n'
            '    }\n'
            '  }\n'
            '}\n'
            '\n'
            'resource "google_cloud_run_service_iam_member" "' + agent_name + '" {\n'
            '  service  = google_cloud_run_service.' + agent_name + '.name\n'
            '  role     = "roles/run.invoker"\n'
            '  member   = "serviceAccount:${google_service_account.agent.email}"\n'
            '  location = var.gcp_region\n'
            '}\n'
        )
        main_tf_content += service_block

    (out_dir / "main.tf").write_text(main_tf_content, encoding="utf-8")
    console.print("  [green]✓[/] main.tf")

    # Generate variables.tf
    variables_tf_content = """variable "gcp_project" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  sensitive   = true
}
"""
    (out_dir / "variables.tf").write_text(variables_tf_content, encoding="utf-8")
    console.print("  [green]✓[/] variables.tf")

    # Generate outputs.tf
    outputs_tf_content = """output "agent_urls" {
  description = "URLs of deployed agent services"
  value = {
"""
    for agent in blueprint.agents:
        outputs_tf_content += (
            f'    {agent.name} = google_cloud_run_service.{agent.name}.status[0].url\n'
        )

    outputs_tf_content += """  }
}
"""
    (out_dir / "outputs.tf").write_text(outputs_tf_content, encoding="utf-8")
    console.print("  [green]✓[/] outputs.tf")

    # Generate iam.tf for GCP
    iam_tf_content = """# Service Account for agents
resource "google_service_account" "agent" {
  account_id   = "clean-agents-sa"
  display_name = "Clean Agents Service Account"
}

# Secret Manager for API keys
resource "google_secret_manager_secret" "anthropic_key" {
  secret_id = "clean-agents-anthropic-api-key"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "anthropic_key" {
  secret      = google_secret_manager_secret.anthropic_key.id
  secret_data = var.anthropic_api_key
}

# Grant service account access to secret
resource "google_secret_manager_secret_iam_member" "agent" {
  secret_id = google_secret_manager_secret.anthropic_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent.email}"
}

# Cloud Logging
resource "google_logging_project_sink" "clean_agents" {
  name        = "clean-agents-sink"
  destination = "logging.googleapis.com/projects/${var.gcp_project}/logs/clean-agents"
}
"""
    (out_dir / "iam.tf").write_text(iam_tf_content, encoding="utf-8")
    console.print("  [green]✓[/] iam.tf")


def _export_cloudformation(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate AWS CloudFormation template."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate CloudFormation template
    cf_content = """AWSTemplateFormatVersion: '2010-09-09'
Description: 'CloudFormation template for Clean-Agents deployment'

Parameters:
  VpcId:
    Type: AWS::EC2::VPC::Id
    Description: VPC ID for deployment
  SubnetIds:
    Type: List<AWS::EC2::Subnet::Id>
    Description: Subnets for ALB and ECS
  ECRRegistry:
    Type: String
    Description: ECR registry URL

Resources:
  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: clean-agents-cluster
      ClusterSettings:
        - Name: containerInsights
          Value: enabled

  # CloudWatch Log Group
  ECSLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: /ecs/clean-agents
      RetentionInDays: 7

  # IAM Role for ECS Task Execution
  ECSTaskExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ecs-tasks.amazonaws.com
            Action: 'sts:AssumeRole'
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

  # IAM Role for ECS Task (application level)
  ECSTaskRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ecs-tasks.amazonaws.com
            Action: 'sts:AssumeRole'

  # Security Group for ALB
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ALB
      VpcId: !Ref VpcId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0

  # Security Group for ECS Tasks
  ECSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ECS tasks
      VpcId: !Ref VpcId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 8000
          ToPort: 8000
          SourceSecurityGroupId: !Ref ALBSecurityGroup

  # Application Load Balancer
  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: clean-agents-alb
      Subnets: !Ref SubnetIds
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Scheme: internet-facing

  # Target Group
  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: clean-agents-tg
      Port: 8000
      Protocol: HTTP
      VpcId: !Ref VpcId
      TargetType: ip
      HealthCheckEnabled: true
      HealthCheckPath: /
      HealthCheckProtocol: HTTP
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 3
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 2

  # Listener
  Listener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref LoadBalancer
      Port: 80
      Protocol: HTTP
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup

"""

    # Add ECS Services for each agent
    for agent in blueprint.agents:
        cf_content += f"""
  # Task Definition for {agent.name}
  TaskDefinition{agent.name.title()}:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: clean-agents-{agent.name}
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: '256'
      Memory: '512'
      ExecutionRoleArn: !GetAtt ECSTaskExecutionRole.Arn
      TaskRoleArn: !GetAtt ECSTaskRole.Arn
      ContainerDefinitions:
        - Name: {agent.name}
          Image: !Sub '${{ECRRegistry}}/{agent.name}:latest'
          Essential: true
          PortMappings:
            - ContainerPort: 8000
              Protocol: tcp
          Environment:
            - Name: AGENT_NAME
              Value: {agent.name}
            - Name: MODEL
              Value: {agent.model.primary}
            - Name: TOKEN_BUDGET
              Value: {agent.token_budget}
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: !Ref ECSLogGroup
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs

  # ECS Service for {agent.name}
  Service{agent.name.title()}:
    Type: AWS::ECS::Service
    DependsOn: Listener
    Properties:
      ServiceName: clean-agents-{agent.name}
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition{agent.name.title()}
      DesiredCount: 1
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          AssignPublicIp: DISABLED
          SecurityGroups:
            - !Ref ECSSecurityGroup
          Subnets: !Ref SubnetIds
      LoadBalancers:
        - ContainerName: {agent.name}
          ContainerPort: 8000
          TargetGroupArn: !Ref TargetGroup

"""

    cf_content += """
Outputs:
  LoadBalancerDNS:
    Description: DNS name of the Load Balancer
    Value: !GetAtt LoadBalancer.DNSName
  ECSClusterArn:
    Description: ARN of the ECS Cluster
    Value: !GetAtt ECSCluster.ClusterArn
"""

    (out_dir / "template.yaml").write_text(cf_content, encoding="utf-8")
    console.print("  [green]✓[/] template.yaml")

    # Generate parameters file
    params_content = """VpcId=vpc-xxxxxxxxx
SubnetIds=subnet-xxxxxxxxx,subnet-yyyyyyyyy
ECRRegistry=123456789.dkr.ecr.us-east-1.amazonaws.com
"""
    (out_dir / "parameters.txt").write_text(params_content, encoding="utf-8")
    console.print("  [green]✓[/] parameters.txt")
