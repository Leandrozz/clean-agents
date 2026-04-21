"""Tests for the export command."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from clean_agents.cli.main import app
from clean_agents.core.blueprint import Blueprint, InfraConfig

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that gets cleaned up."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def blueprint_with_agents(temp_dir) -> Blueprint:
    """Create a test blueprint with agents."""
    bp = Blueprint(
        name="test-system",
        description="Test agent system",
        agents=[
            {
                "name": "orchestrator",
                "role": "Coordinate between agents",
                "agent_type": "orchestrator",
                "model": {"primary": "claude-sonnet-4-6"},
                "token_budget": 4096,
            },
            {
                "name": "researcher",
                "role": "Research and gather information",
                "agent_type": "specialist",
                "model": {"primary": "claude-opus-4-6"},
                "token_budget": 8192,
                "dependencies": [],
            },
            {
                "name": "writer",
                "role": "Write and synthesize information",
                "agent_type": "specialist",
                "model": {"primary": "claude-sonnet-4-6"},
                "token_budget": 4096,
                "dependencies": ["researcher"],
            },
        ],
        infrastructure=InfraConfig(
            message_queue="redis",
            observability="langfuse",
        ),
    )

    # Save blueprint
    bp_path = temp_dir / "blueprint.yaml"
    bp.save(bp_path)
    return bp


class TestExportDocker:
    """Test Docker export functionality."""

    def test_export_docker_creates_files(self, temp_dir, blueprint_with_agents):
        """Test that docker export creates all necessary files."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "docker",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0, f"Export failed: {result.stdout}"

        # Check files exist
        assert (output_dir / "docker-compose.yml").exists()
        assert (output_dir / ".env.example").exists()
        assert (output_dir / "Makefile").exists()

        # Check Dockerfiles for each agent
        assert (output_dir / "Dockerfile.orchestrator").exists()
        assert (output_dir / "Dockerfile.researcher").exists()
        assert (output_dir / "Dockerfile.writer").exists()

    def test_export_docker_compose_has_agents(self, temp_dir, blueprint_with_agents):
        """Test that docker-compose includes all agents."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "docker",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        compose_content = (output_dir / "docker-compose.yml").read_text()
        assert "orchestrator:" in compose_content
        assert "researcher:" in compose_content
        assert "writer:" in compose_content
        assert "postgres:" in compose_content
        assert "redis:" in compose_content
        assert "langfuse:" in compose_content

    def test_export_docker_has_dependencies(self, temp_dir, blueprint_with_agents):
        """Test that docker-compose reflects agent dependencies."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "docker",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        compose_content = (output_dir / "docker-compose.yml").read_text()
        # Writer depends on researcher
        assert "writer:" in compose_content
        assert "researcher:" in compose_content

    def test_export_docker_dockerfile_valid(self, temp_dir, blueprint_with_agents):
        """Test that generated Dockerfiles are valid."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "docker",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        dockerfile = (output_dir / "Dockerfile.researcher").read_text()
        assert "FROM python:3.11-slim" in dockerfile
        assert "WORKDIR /app" in dockerfile
        assert "AGENT_NAME=researcher" in dockerfile
        assert "MODEL=claude-opus-4-6" in dockerfile
        assert "TOKEN_BUDGET=8192" in dockerfile

    def test_export_docker_makefile_valid(self, temp_dir, blueprint_with_agents):
        """Test that generated Makefile is valid."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "docker",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        makefile = (output_dir / "Makefile").read_text()
        assert "up:" in makefile
        assert "down:" in makefile
        assert "logs:" in makefile
        assert "docker-compose up -d" in makefile


class TestExportK8s:
    """Test Kubernetes export functionality."""

    def test_export_k8s_creates_files(self, temp_dir, blueprint_with_agents):
        """Test that k8s export creates all necessary files."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "k8s",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0, f"Export failed: {result.stdout}"

        # Check files exist
        assert (output_dir / "namespace.yaml").exists()
        assert (output_dir / "configmap.yaml").exists()
        assert (output_dir / "secret.yaml").exists()
        assert (output_dir / "kustomization.yaml").exists()

    def test_export_k8s_has_deployments(self, temp_dir, blueprint_with_agents):
        """Test that k8s export creates deployment for each agent."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "k8s",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        # Check deployment files
        assert (output_dir / "deployment-orchestrator.yaml").exists()
        assert (output_dir / "deployment-researcher.yaml").exists()
        assert (output_dir / "deployment-writer.yaml").exists()

    def test_export_k8s_has_services(self, temp_dir, blueprint_with_agents):
        """Test that k8s export creates service for each agent."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "k8s",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        # Check service files
        assert (output_dir / "service-orchestrator.yaml").exists()
        assert (output_dir / "service-researcher.yaml").exists()
        assert (output_dir / "service-writer.yaml").exists()

    def test_export_k8s_deployment_valid(self, temp_dir, blueprint_with_agents):
        """Test that generated K8s deployments are valid YAML."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "k8s",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        deployment_content = (output_dir / "deployment-researcher.yaml").read_text()
        assert "apiVersion: apps/v1" in deployment_content
        assert "kind: Deployment" in deployment_content
        assert "name: researcher" in deployment_content
        assert "value: \"claude-opus-4-6\"" in deployment_content
        assert "resources:" in deployment_content

    def test_export_k8s_kustomization_valid(self, temp_dir, blueprint_with_agents):
        """Test that generated kustomization.yaml is valid."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "k8s",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        kustom_content = (output_dir / "kustomization.yaml").read_text()
        assert "apiVersion: kustomize.config.k8s.io/v1beta1" in kustom_content
        assert "kind: Kustomization" in kustom_content
        assert "resources:" in kustom_content
        assert "deployment-researcher.yaml" in kustom_content


class TestExportTerraform:
    """Test Terraform export functionality."""

    def test_export_terraform_aws_creates_files(self, temp_dir, blueprint_with_agents):
        """Test that terraform-aws export creates all necessary files."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "terraform-aws",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0, f"Export failed: {result.stdout}"

        # Check files exist
        assert (output_dir / "main.tf").exists()
        assert (output_dir / "variables.tf").exists()
        assert (output_dir / "outputs.tf").exists()
        assert (output_dir / "iam.tf").exists()
        assert (output_dir / "terraform.tfvars.example").exists()

    def test_export_terraform_aws_has_agents(self, temp_dir, blueprint_with_agents):
        """Test that terraform aws includes all agents."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "terraform-aws",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        main_content = (output_dir / "main.tf").read_text()
        assert 'resource "aws_ecs_task_definition" "orchestrator"' in main_content
        assert 'resource "aws_ecs_service" "orchestrator"' in main_content
        assert 'resource "aws_ecs_task_definition" "researcher"' in main_content
        assert 'resource "aws_ecs_service" "researcher"' in main_content
        assert 'resource "aws_ecs_task_definition" "writer"' in main_content

    def test_export_terraform_aws_iam(self, temp_dir, blueprint_with_agents):
        """Test that terraform aws includes IAM configuration."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "terraform-aws",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        iam_content = (output_dir / "iam.tf").read_text()
        assert "aws_iam_role" in iam_content
        assert "aws_iam_role_policy" in iam_content
        assert "AmazonECSTaskExecutionRolePolicy" in iam_content

    def test_export_terraform_gcp_creates_files(self, temp_dir, blueprint_with_agents):
        """Test that terraform-gcp export creates necessary files."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "terraform-gcp",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0, f"Export failed: {result.stdout}"

        # Check files exist
        assert (output_dir / "main.tf").exists()
        assert (output_dir / "variables.tf").exists()
        assert (output_dir / "outputs.tf").exists()
        assert (output_dir / "iam.tf").exists()

    def test_export_terraform_gcp_cloud_run(self, temp_dir, blueprint_with_agents):
        """Test that terraform gcp uses Cloud Run."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "terraform-gcp",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        main_content = (output_dir / "main.tf").read_text()
        assert "google_cloud_run_service" in main_content
        assert "google_service_account" in main_content


class TestExportCloudFormation:
    """Test CloudFormation export functionality."""

    def test_export_cloudformation_creates_files(self, temp_dir, blueprint_with_agents):
        """Test that cloudformation export creates template."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "cloudformation",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0, f"Export failed: {result.stdout}"

        # Check files exist
        assert (output_dir / "template.yaml").exists()
        assert (output_dir / "parameters.txt").exists()

    def test_export_cloudformation_has_agents(self, temp_dir, blueprint_with_agents):
        """Test that cloudformation template includes all agents."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "cloudformation",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        cf_content = (output_dir / "template.yaml").read_text()
        assert "AWSTemplateFormatVersion" in cf_content
        assert "TaskDefinitionOrchestrator:" in cf_content
        assert "ServiceOrchestrator:" in cf_content
        assert "TaskDefinitionResearcher:" in cf_content
        assert "TaskDefinitionWriter:" in cf_content

    def test_export_cloudformation_ecs(self, temp_dir, blueprint_with_agents):
        """Test that cloudformation uses ECS."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "cloudformation",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0

        cf_content = (output_dir / "template.yaml").read_text()
        assert "AWS::ECS::Cluster" in cf_content
        assert "AWS::ECS::TaskDefinition" in cf_content
        assert "AWS::ECS::Service" in cf_content


class TestExportErrorHandling:
    """Test error handling in export command."""

    def test_export_no_blueprint_fails(self, temp_dir):
        """Test that export fails when no blueprint is found."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "docker",
                "--path",
                str(temp_dir / "nonexistent.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code != 0
        assert "No blueprint found" in result.stdout

    def test_export_invalid_target_fails(self, temp_dir, blueprint_with_agents):
        """Test that export fails with invalid target."""
        output_dir = temp_dir / "deploy"
        result = runner.invoke(
            app,
            [
                "export",
                "invalid-target",
                "--path",
                str(temp_dir / "blueprint.yaml"),
                "--output",
                str(output_dir),
            ],
        )
        assert result.exit_code != 0
        assert "Unknown target" in result.stdout
