"""Tests for scaffold command and scaffold generators."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from clean_agents.cli.scaffold_cmd import (
    _scaffold_autogen,
    _scaffold_docker,
    _scaffold_llamaindex,
    _scaffold_semantic_kernel,
    _scaffold_terraform,
)
from clean_agents.core.blueprint import Blueprint


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that gets cleaned up."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_blueprint():
    """Create a sample blueprint for testing."""
    return Blueprint(
        name="test-agents",
        description="Test agent system",
        agents=[
            {
                "name": "orchestrator",
                "role": "Coordinate and delegate tasks",
                "agent_type": "orchestrator",
                "model": {"primary": "gpt-4"},
                "reasoning": "react",
                "token_budget": 4000,
                "is_orchestrator": True,
            },
            {
                "name": "researcher",
                "role": "Research and gather information",
                "agent_type": "specialist",
                "model": {"primary": "gpt-4"},
                "reasoning": "tree-of-thoughts",
                "token_budget": 2000,
                "is_orchestrator": False,
            },
            {
                "name": "writer",
                "role": "Write and format content",
                "agent_type": "specialist",
                "model": {"primary": "gpt-4"},
                "reasoning": "reflection",
                "token_budget": 3000,
                "is_orchestrator": False,
            },
        ],
    )


class TestScaffoldAutogen:
    """Test AutoGen scaffold generation."""

    def test_scaffold_autogen_creates_agents_file(self, temp_dir, sample_blueprint):
        """Test that autogen scaffold creates agents.py."""
        _scaffold_autogen(sample_blueprint, temp_dir)

        agents_file = temp_dir / "agents.py"
        assert agents_file.exists(), "agents.py was not created"

        content = agents_file.read_text()
        assert "AssistantAgent" in content
        assert "UserProxyAgent" in content
        assert "GroupChat" in content
        assert "from autogen import" in content

    def test_scaffold_autogen_includes_all_agents(self, temp_dir, sample_blueprint):
        """Test that all agents are included in autogen scaffold."""
        _scaffold_autogen(sample_blueprint, temp_dir)

        agents_file = temp_dir / "agents.py"
        content = agents_file.read_text()

        for agent in sample_blueprint.agents:
            assert agent.name in content, f"Agent {agent.name} not found in scaffold"

    def test_scaffold_autogen_creates_requirements(self, temp_dir, sample_blueprint):
        """Test that requirements.txt is created with autogen."""
        _scaffold_autogen(sample_blueprint, temp_dir)

        reqs_file = temp_dir / "requirements.txt"
        assert reqs_file.exists(), "requirements.txt was not created"

        content = reqs_file.read_text()
        assert "pyautogen" in content

    def test_scaffold_autogen_creates_oai_config(self, temp_dir, sample_blueprint):
        """Test that OAI_CONFIG_LIST.json is created."""
        _scaffold_autogen(sample_blueprint, temp_dir)

        config_file = temp_dir / "OAI_CONFIG_LIST.json"
        assert config_file.exists(), "OAI_CONFIG_LIST.json was not created"

        content = config_file.read_text()
        assert "model" in content
        assert "api_key" in content


class TestScaffoldSemanticKernel:
    """Test Semantic Kernel scaffold generation."""

    def test_scaffold_semantic_kernel_creates_agents_file(self, temp_dir, sample_blueprint):
        """Test that semantic kernel scaffold creates agents.py."""
        _scaffold_semantic_kernel(sample_blueprint, temp_dir)

        agents_file = temp_dir / "agents.py"
        assert agents_file.exists(), "agents.py was not created"

        content = agents_file.read_text()
        assert "semantic_kernel" in content
        assert "kernel = sk.Kernel()" in content

    def test_scaffold_semantic_kernel_includes_agents(self, temp_dir, sample_blueprint):
        """Test that all agents are included."""
        _scaffold_semantic_kernel(sample_blueprint, temp_dir)

        agents_file = temp_dir / "agents.py"
        content = agents_file.read_text()

        for agent in sample_blueprint.agents:
            assert agent.name.lower() in content.lower()

    def test_scaffold_semantic_kernel_creates_requirements(self, temp_dir, sample_blueprint):
        """Test that requirements.txt is created."""
        _scaffold_semantic_kernel(sample_blueprint, temp_dir)

        reqs_file = temp_dir / "requirements.txt"
        assert reqs_file.exists(), "requirements.txt was not created"

        content = reqs_file.read_text()
        assert "semantic-kernel" in content

    def test_scaffold_semantic_kernel_has_run_agents_function(self, temp_dir, sample_blueprint):
        """Test that run_agents function is defined."""
        _scaffold_semantic_kernel(sample_blueprint, temp_dir)

        agents_file = temp_dir / "agents.py"
        content = agents_file.read_text()

        assert "def run_agents()" in content


class TestScaffoldLlamaIndex:
    """Test LlamaIndex scaffold generation."""

    def test_scaffold_llamaindex_creates_workflow_file(self, temp_dir, sample_blueprint):
        """Test that llamaindex scaffold creates workflow.py."""
        _scaffold_llamaindex(sample_blueprint, temp_dir)

        workflow_file = temp_dir / "workflow.py"
        assert workflow_file.exists(), "workflow.py was not created"

        content = workflow_file.read_text()
        assert "from llama_index.core.workflow import Workflow" in content
        assert "@step" in content

    def test_scaffold_llamaindex_includes_agent_steps(self, temp_dir, sample_blueprint):
        """Test that workflow includes steps for each agent."""
        _scaffold_llamaindex(sample_blueprint, temp_dir)

        workflow_file = temp_dir / "workflow.py"
        content = workflow_file.read_text()

        for agent in sample_blueprint.agents:
            assert f"{agent.name}_step" in content

    def test_scaffold_llamaindex_creates_requirements(self, temp_dir, sample_blueprint):
        """Test that requirements.txt is created."""
        _scaffold_llamaindex(sample_blueprint, temp_dir)

        reqs_file = temp_dir / "requirements.txt"
        assert reqs_file.exists(), "requirements.txt was not created"

        content = reqs_file.read_text()
        assert "llama-index" in content

    def test_scaffold_llamaindex_has_async_workflow(self, temp_dir, sample_blueprint):
        """Test that workflow is async."""
        _scaffold_llamaindex(sample_blueprint, temp_dir)

        workflow_file = temp_dir / "workflow.py"
        content = workflow_file.read_text()

        assert "async def" in content
        assert "await" in content


class TestScaffoldDocker:
    """Test Docker scaffold generation."""

    def test_scaffold_docker_creates_dockerfile(self, temp_dir, sample_blueprint):
        """Test that Dockerfile is created."""
        _scaffold_docker(sample_blueprint, temp_dir)

        dockerfile = temp_dir / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile was not created"

        content = dockerfile.read_text()
        assert "FROM python:3.11-slim" in content
        assert "HEALTHCHECK" in content
        assert "requirements.txt" in content

    def test_scaffold_docker_creates_docker_compose(self, temp_dir, sample_blueprint):
        """Test that docker-compose.yml is created."""
        _scaffold_docker(sample_blueprint, temp_dir)

        compose_file = temp_dir / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml was not created"

        content = compose_file.read_text()
        assert "version:" in content
        assert "services:" in content
        assert "redis:" in content
        assert "postgres:" in content

    def test_scaffold_docker_includes_all_services(self, temp_dir, sample_blueprint):
        """Test that all agents are included as services."""
        _scaffold_docker(sample_blueprint, temp_dir)

        compose_file = temp_dir / "docker-compose.yml"
        content = compose_file.read_text()

        for agent in sample_blueprint.agents:
            assert agent.name in content

    def test_scaffold_docker_creates_env_example(self, temp_dir, sample_blueprint):
        """Test that .env.example is created."""
        _scaffold_docker(sample_blueprint, temp_dir)

        env_file = temp_dir / ".env.example"
        assert env_file.exists(), ".env.example was not created"

        content = env_file.read_text()
        assert "OPENAI_API_KEY" in content
        assert "POSTGRES_PASSWORD" in content
        assert "LOG_LEVEL" in content

    def test_scaffold_docker_creates_dockerignore(self, temp_dir, sample_blueprint):
        """Test that .dockerignore is created."""
        _scaffold_docker(sample_blueprint, temp_dir)

        dockerignore = temp_dir / ".dockerignore"
        assert dockerignore.exists(), ".dockerignore was not created"

        content = dockerignore.read_text()
        assert "__pycache__" in content
        assert ".env" in content
        assert ".git" in content

    def test_scaffold_docker_has_healthcheck(self, temp_dir, sample_blueprint):
        """Test that Dockerfile includes healthcheck."""
        _scaffold_docker(sample_blueprint, temp_dir)

        dockerfile = temp_dir / "Dockerfile"
        content = dockerfile.read_text()

        assert "HEALTHCHECK" in content
        assert "curl" in content

    def test_scaffold_docker_compose_has_networks(self, temp_dir, sample_blueprint):
        """Test that docker-compose has network configuration."""
        _scaffold_docker(sample_blueprint, temp_dir)

        compose_file = temp_dir / "docker-compose.yml"
        content = compose_file.read_text()

        assert "networks:" in content
        assert "agent-network" in content


class TestScaffoldTerraform:
    """Test Terraform scaffold generation."""

    def test_scaffold_terraform_creates_main_tf(self, temp_dir, sample_blueprint):
        """Test that main.tf is created."""
        _scaffold_terraform(sample_blueprint, temp_dir)

        main_tf = temp_dir / "terraform" / "main.tf"
        assert main_tf.exists(), "terraform/main.tf was not created"

        content = main_tf.read_text()
        assert "aws_ecs_cluster" in content
        assert "aws_ecs_task_definition" in content
        assert "aws_ecs_service" in content

    def test_scaffold_terraform_creates_variables_tf(self, temp_dir, sample_blueprint):
        """Test that variables.tf is created."""
        _scaffold_terraform(sample_blueprint, temp_dir)

        variables_tf = temp_dir / "terraform" / "variables.tf"
        assert variables_tf.exists(), "terraform/variables.tf was not created"

        content = variables_tf.read_text()
        assert "variable \"aws_region\"" in content
        assert "variable \"project_name\"" in content
        assert "variable \"task_cpu\"" in content

    def test_scaffold_terraform_creates_outputs_tf(self, temp_dir, sample_blueprint):
        """Test that outputs.tf is created."""
        _scaffold_terraform(sample_blueprint, temp_dir)

        outputs_tf = temp_dir / "terraform" / "outputs.tf"
        assert outputs_tf.exists(), "terraform/outputs.tf was not created"

        content = outputs_tf.read_text()
        assert "output \"ecs_cluster_name\"" in content
        assert "output \"ecs_service_name\"" in content

    def test_scaffold_terraform_creates_tfvars_example(self, temp_dir, sample_blueprint):
        """Test that terraform.tfvars.example is created."""
        _scaffold_terraform(sample_blueprint, temp_dir)

        tfvars = temp_dir / "terraform" / "terraform.tfvars.example"
        assert tfvars.exists(), "terraform/terraform.tfvars.example was not created"

        content = tfvars.read_text()
        assert "aws_region" in content
        assert "project_name" in content
        assert "vpc_id" in content

    def test_scaffold_terraform_has_fargate_configuration(self, temp_dir, sample_blueprint):
        """Test that Terraform uses Fargate launch type."""
        _scaffold_terraform(sample_blueprint, temp_dir)

        main_tf = temp_dir / "terraform" / "main.tf"
        content = main_tf.read_text()

        assert "FARGATE" in content
        assert "launch_type" in content

    def test_scaffold_terraform_includes_secrets_manager(self, temp_dir, sample_blueprint):
        """Test that Terraform includes AWS Secrets Manager."""
        _scaffold_terraform(sample_blueprint, temp_dir)

        main_tf = temp_dir / "terraform" / "main.tf"
        content = main_tf.read_text()

        assert "aws_secretsmanager_secret" in content
        assert "OPENAI_API_KEY" in content

    def test_scaffold_terraform_has_iam_roles(self, temp_dir, sample_blueprint):
        """Test that Terraform creates IAM roles."""
        _scaffold_terraform(sample_blueprint, temp_dir)

        main_tf = temp_dir / "terraform" / "main.tf"
        content = main_tf.read_text()

        assert "aws_iam_role" in content
        assert "ecs_task_execution_role" in content
        assert "ecs_task_role" in content

    def test_scaffold_terraform_has_security_group(self, temp_dir, sample_blueprint):
        """Test that Terraform creates security groups."""
        _scaffold_terraform(sample_blueprint, temp_dir)

        main_tf = temp_dir / "terraform" / "main.tf"
        content = main_tf.read_text()

        assert "aws_security_group" in content
        assert "ingress" in content

    def test_scaffold_terraform_includes_logging(self, temp_dir, sample_blueprint):
        """Test that Terraform includes CloudWatch logging."""
        _scaffold_terraform(sample_blueprint, temp_dir)

        main_tf = temp_dir / "terraform" / "main.tf"
        content = main_tf.read_text()

        assert "aws_cloudwatch_log_group" in content
        assert "awslogs" in content


class TestScaffoldIntegration:
    """Integration tests for scaffold generation."""

    def test_scaffold_autogen_with_docker(self, temp_dir, sample_blueprint):
        """Test generating autogen scaffold with Docker."""
        _scaffold_autogen(sample_blueprint, temp_dir)
        _scaffold_docker(sample_blueprint, temp_dir)

        # Check that both autogen and docker files exist
        assert (temp_dir / "agents.py").exists()
        assert (temp_dir / "Dockerfile").exists()
        assert (temp_dir / "docker-compose.yml").exists()

    def test_scaffold_semantic_kernel_with_terraform(self, temp_dir, sample_blueprint):
        """Test generating semantic kernel with Terraform."""
        _scaffold_semantic_kernel(sample_blueprint, temp_dir)
        _scaffold_terraform(sample_blueprint, temp_dir)

        # Check that both semantic kernel and terraform files exist
        assert (temp_dir / "agents.py").exists()
        assert (temp_dir / "terraform" / "main.tf").exists()

    def test_scaffold_llamaindex_with_all_infra(self, temp_dir, sample_blueprint):
        """Test generating llamaindex with both Docker and Terraform."""
        _scaffold_llamaindex(sample_blueprint, temp_dir)
        _scaffold_docker(sample_blueprint, temp_dir)
        _scaffold_terraform(sample_blueprint, temp_dir)

        # Check that all expected files exist
        assert (temp_dir / "workflow.py").exists()
        assert (temp_dir / "Dockerfile").exists()
        assert (temp_dir / "terraform" / "main.tf").exists()

    def test_scaffold_files_are_valid_python_syntax(self, temp_dir, sample_blueprint):
        """Test that generated Python files have valid syntax."""
        import ast

        _scaffold_autogen(sample_blueprint, temp_dir)
        _scaffold_semantic_kernel(sample_blueprint, temp_dir)
        _scaffold_llamaindex(sample_blueprint, temp_dir)

        python_files = [
            temp_dir / "agents.py",  # from autogen
            temp_dir / "workflow.py",  # from llamaindex (may be overwritten)
        ]

        for py_file in python_files:
            if py_file.exists():
                content = py_file.read_text()
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    pytest.fail(f"Invalid Python syntax in {py_file}: {e}")

    def test_scaffold_output_directories_structure(self, temp_dir, sample_blueprint):
        """Test that output directory structure is correct."""
        _scaffold_autogen(sample_blueprint, temp_dir)
        _scaffold_docker(sample_blueprint, temp_dir)
        _scaffold_terraform(sample_blueprint, temp_dir)

        # Check directory structure
        assert temp_dir.exists()
        assert (temp_dir / "terraform").is_dir()

        # Check required files exist
        required_files = [
            "agents.py",
            "requirements.txt",
            "OAI_CONFIG_LIST.json",
            "Dockerfile",
            "docker-compose.yml",
            ".env.example",
            ".dockerignore",
        ]

        for filename in required_files:
            assert (temp_dir / filename).exists(), f"Missing {filename}"

        tf_files = ["main.tf", "variables.tf", "outputs.tf", "terraform.tfvars.example"]
        for filename in tf_files:
            assert (temp_dir / "terraform" / filename).exists(), f"Missing terraform/{filename}"
