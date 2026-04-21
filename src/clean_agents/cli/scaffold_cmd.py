"""clean-agents scaffold — generate framework-specific starter code."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from clean_agents.core.blueprint import Blueprint
from clean_agents.core.config import Config

console = Console()


def scaffold_cmd(
    path: str = typer.Option("", "--path", "-p", help="Blueprint file path"),
    output: str = typer.Option(
        "./generated", "--output", "-o", help="Output directory"
    ),
    framework: str = typer.Option(
        "",
        "--framework",
        "-f",
        help="Override framework (langgraph, crewai, autogen, semantic-kernel, etc.)",
    ),
    docker: bool = typer.Option(False, "--docker", help="Also generate Docker files"),
    terraform: bool = typer.Option(
        False, "--terraform", help="Also generate Terraform files"
    ),
) -> None:
    """Generate framework-specific starter code from the current blueprint."""
    config = Config.discover()
    bp_path = Path(path) if path else config.blueprint_path()

    if not bp_path.exists():
        console.print("[red]Error:[/] No blueprint found. Run [bold]clean-agents design[/] first.")
        raise typer.Exit(1)

    blueprint = Blueprint.load(bp_path)
    target_framework = framework or blueprint.framework
    out_dir = Path(output)

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Scaffold[/] — Generating {target_framework} starter code",
        border_style="cyan",
    ))
    console.print()

    if target_framework == "langgraph":
        _scaffold_langgraph(blueprint, out_dir)
    elif target_framework == "crewai":
        _scaffold_crewai(blueprint, out_dir)
    elif target_framework in ("claude-agent-sdk", "openai-agents-sdk"):
        _scaffold_sdk(blueprint, out_dir, target_framework)
    elif target_framework == "autogen":
        _scaffold_autogen(blueprint, out_dir)
    elif target_framework == "semantic-kernel":
        _scaffold_semantic_kernel(blueprint, out_dir)
    elif target_framework == "llamaindex":
        _scaffold_llamaindex(blueprint, out_dir)
    else:
        _scaffold_generic(blueprint, out_dir, target_framework)

    if docker:
        _scaffold_docker(blueprint, out_dir)

    if terraform:
        _scaffold_terraform(blueprint, out_dir)

    console.print(f"\n[green]✓[/] Scaffold generated in [bold]{out_dir}[/]")
    console.print()
    console.print("[dim]Next steps:[/]")
    console.print(f"  cd {out_dir}")
    console.print("  pip install -r requirements.txt")
    console.print("  # Review and customize generated agents")
    if docker:
        console.print("  docker-compose up")
    if terraform:
        console.print("  terraform init && terraform plan")


def _scaffold_langgraph(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate LangGraph scaffold."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Main graph file
    imports = [
        "from langgraph.graph import StateGraph, END",
        "from langgraph.prebuilt import ToolNode",
        "from typing import TypedDict, Annotated",
        "import operator",
    ]

    state_fields = ["messages: Annotated[list, operator.add]"]
    for agent in blueprint.agents:
        state_fields.append(f'{agent.name}_output: str = ""')

    nodes = []

    for agent in blueprint.agents:
        nodes.append(f"""
def {agent.name}_node(state: State) -> dict:
    \"\"\"Agent: {agent.role}\"\"\"
    # TODO: Implement {agent.name} logic
    # Model: {agent.model.primary}
    # Reasoning: {agent.reasoning.value}
    return {{{repr(agent.name + '_output')}: "placeholder"}}
""")

    # Build graph construction
    graph_code = "\n# Build graph\nbuilder = StateGraph(State)\n"
    for agent in blueprint.agents:
        graph_code += f'builder.add_node("{agent.name}", {agent.name}_node)\n'

    # Connect orchestrator to specialists
    orchestrator = blueprint.get_orchestrator()
    if orchestrator:
        graph_code += f'\nbuilder.set_entry_point("{orchestrator.name}")\n'
        for agent in blueprint.agents:
            if agent.name != orchestrator.name:
                graph_code += f'builder.add_edge("{orchestrator.name}", "{agent.name}")\n'
                graph_code += f'builder.add_edge("{agent.name}", END)\n'
    else:
        if blueprint.agents:
            first_agent = blueprint.agents[0].name
            graph_code += f'\nbuilder.set_entry_point("{first_agent}")\n'
            for i in range(len(blueprint.agents) - 1):
                curr_agent = blueprint.agents[i].name
                next_agent = blueprint.agents[i + 1].name
                graph_code += f'builder.add_edge("{curr_agent}", "{next_agent}")\n'
            last_agent = blueprint.agents[-1].name
            graph_code += f'builder.add_edge("{last_agent}", END)\n'

    graph_code += "\ngraph = builder.compile()\n"

    # Write main file
    main_content = "\n".join(imports) + "\n\n"
    main_content += f"# Generated by CLean-agents for: {blueprint.name}\n"
    main_content += f"# Pattern: {blueprint.pattern.value}\n\n"
    main_content += "class State(TypedDict):\n"
    for field in state_fields:
        main_content += f"    {field}\n"
    main_content += "\n"
    main_content += "\n".join(nodes)
    main_content += graph_code

    (out_dir / "graph.py").write_text(main_content, encoding="utf-8")
    console.print("  [green]✓[/] graph.py — Main LangGraph definition")

    # Write agent prompt files
    prompts_dir = out_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    for agent in blueprint.agents:
        prompt = f"# {agent.name}\n\n{agent.role}\n\n"
        prompt += f"Model: {agent.model.primary}\nReasoning: {agent.reasoning.value}\n"
        (prompts_dir / f"{agent.name}.md").write_text(prompt, encoding="utf-8")

    console.print("  [green]✓[/] prompts/ — Agent system prompts")

    # Requirements file
    reqs = "langgraph>=0.2\nlangchain-anthropic>=0.2\nlangchain-openai>=0.2\n"
    (out_dir / "requirements.txt").write_text(reqs, encoding="utf-8")
    console.print("  [green]✓[/] requirements.txt")


def _scaffold_crewai(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate CrewAI scaffold."""
    out_dir.mkdir(parents=True, exist_ok=True)

    content = f"""# Generated by CLean-agents for: {blueprint.name}
from crewai import Agent, Task, Crew, Process

"""
    for agent in blueprint.agents:
        content += f"""
{agent.name} = Agent(
    role="{agent.name}",
    goal="{agent.role}",
    backstory="You are a specialized {agent.agent_type} agent.",
    llm="{agent.model.primary}",
    verbose=True,
)
"""

    content += "\n# Tasks\ntasks = [\n"
    for agent in blueprint.agents:
        if not agent.is_orchestrator():
            content += f"""    Task(
        description="{agent.role}",
        agent={agent.name},
        expected_output="Structured output for {agent.name}",
    ),
"""
    content += "]\n\n"

    orchestrator = blueprint.get_orchestrator()
    process = (
        "Process.hierarchical"
        if orchestrator
        else "Process.sequential"
    )
    manager = f"manager_agent={orchestrator.name}," if orchestrator else ""

    content += f"""crew = Crew(
    agents=[{', '.join(a.name for a in blueprint.agents)}],
    tasks=tasks,
    process={process},
    {manager}
    verbose=True,
)

if __name__ == "__main__":
    result = crew.kickoff()
    print(result)
"""

    (out_dir / "crew.py").write_text(content, encoding="utf-8")
    console.print("  [green]✓[/] crew.py — CrewAI definition")

    reqs = "crewai>=0.60\n"
    (out_dir / "requirements.txt").write_text(reqs, encoding="utf-8")
    console.print("  [green]✓[/] requirements.txt")


def _scaffold_sdk(blueprint: Blueprint, out_dir: Path, sdk: str) -> None:
    """Generate SDK scaffold (Claude or OpenAI)."""
    out_dir.mkdir(parents=True, exist_ok=True)

    if sdk == "claude-agent-sdk":
        content = f"""# Generated by CLean-agents for: {blueprint.name}
import anthropic

client = anthropic.Anthropic()
"""
        for agent in blueprint.agents:
            content += f"""
def run_{agent.name}(input_text: str) -> str:
    \"\"\"Agent: {agent.role}\"\"\"
    response = client.messages.create(
        model="{agent.model.primary}",
        max_tokens={agent.token_budget},
        system="{agent.role}",
        messages=[{{"role": "user", "content": input_text}}],
    )
    return response.content[0].text
"""
    else:
        content = f"""# Generated by CLean-agents for: {blueprint.name}
from openai import OpenAI

client = OpenAI()
"""
        for agent in blueprint.agents:
            content += f"""
def run_{agent.name}(input_text: str) -> str:
    \"\"\"Agent: {agent.role}\"\"\"
    response = client.chat.completions.create(
        model="{agent.model.primary}",
        max_tokens={agent.token_budget},
        messages=[
            {{"role": "system", "content": "{agent.role}"}},
            {{"role": "user", "content": input_text}},
        ],
    )
    return response.choices[0].message.content
"""

    (out_dir / "agents.py").write_text(content, encoding="utf-8")
    console.print("  [green]✓[/] agents.py — Agent definitions")


def _scaffold_generic(blueprint: Blueprint, out_dir: Path, framework: str) -> None:
    """Generate generic scaffold."""
    out_dir.mkdir(parents=True, exist_ok=True)

    content = f"""# Generated by CLean-agents for: {blueprint.name}
# Target framework: {framework}
# Pattern: {blueprint.pattern.value}

# Agent definitions — implement with your framework of choice:
"""
    for agent in blueprint.agents:
        content += f"""
# {agent.name} ({agent.agent_type})
#   Role: {agent.role}
#   Model: {agent.model.primary}
#   Reasoning: {agent.reasoning.value}
#   Token budget: {agent.token_budget}
"""

    (out_dir / "agents_spec.py").write_text(content, encoding="utf-8")
    console.print("  [green]✓[/] agents_spec.py — Agent specifications")


def _scaffold_autogen(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate AutoGen (v0.4+) multi-agent scaffold."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Main agents file
    content = f"""# Generated by CLean-agents for: {blueprint.name}
# AutoGen v0.4+ multi-agent scaffold
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# Configuration for API access
import json
import os

# OAI_CONFIG_LIST should contain API credentials
# Example format:
# [
#     {{
#         "model": "gpt-4",
#         "api_key": "YOUR_API_KEY",
#         "api_base": "https://api.openai.com/v1"
#     }}
# ]

oai_config_list = json.loads(os.getenv("OAI_CONFIG_LIST", "[]"))

# Agent definitions
agents = {{
"""

    for agent in blueprint.agents:
        is_user_proxy = "user" in agent.name.lower() or agent.is_orchestrator()
        if is_user_proxy:
            content += f"""    "{agent.name}": UserProxyAgent(
        name="{agent.name}",
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=10,
        code_execution_config={{"work_dir": "work", "use_docker": False}},
    ),
"""
        else:
            content += f"""    "{agent.name}": AssistantAgent(
        name="{agent.name}",
        system_message="{agent.role}",
        llm_config={{"config_list": oai_config_list, "temperature": 0.7}},
        human_input_mode="NEVER",
    ),
"""

    content += """}}

def create_group_chat():
    \"\"\"Create a group chat with all agents.\"\"\"
    agent_list = list(agents.values())

    groupchat = GroupChat(
        agents=agent_list,
        messages=[],
        max_round=10,
        speaker_selection_method="auto",
    )

    manager = GroupChatManager(groupchat=groupchat, llm_config=oai_config_list[0])
    return manager, agent_list

if __name__ == "__main__":
    manager, agents_list = create_group_chat()
    # Initiate group chat
    user_agent = agents_list[0]
    user_agent.initiate_chat(manager, message="Begin task execution")
"""

    (out_dir / "agents.py").write_text(content, encoding="utf-8")
    console.print("  [green]✓[/] agents.py — AutoGen agent definitions")

    # OAI Config template
    oai_config = """[
    {
        "model": "gpt-4",
        "api_key": "${OPENAI_API_KEY}",
        "api_base": "https://api.openai.com/v1"
    }
]
"""
    (out_dir / "OAI_CONFIG_LIST.json").write_text(oai_config, encoding="utf-8")
    console.print("  [green]✓[/] OAI_CONFIG_LIST.json — API configuration template")

    # Requirements
    reqs = "pyautogen>=0.4\nPython-dotenv>=1.0\n"
    (out_dir / "requirements.txt").write_text(reqs, encoding="utf-8")
    console.print("  [green]✓[/] requirements.txt")


def _scaffold_semantic_kernel(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate Microsoft Semantic Kernel scaffold."""
    out_dir.mkdir(parents=True, exist_ok=True)

    content = f"""# Generated by CLean-agents for: {blueprint.name}
# Microsoft Semantic Kernel scaffold
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from semantic_kernel.core_plugins import ConversationSummaryPlugin
import os

# Initialize kernel
kernel = sk.Kernel()

# Configure LLM
api_key = os.getenv("OPENAI_API_KEY", "")
model_name = os.getenv("MODEL_NAME", "gpt-4")

# Add chat completion service
chat_completion = OpenAIChatCompletion(
    model_id=model_name,
    api_key=api_key,
)
kernel.add_service(chat_completion)

# Add built-in plugins
kernel.add_plugin(ConversationSummaryPlugin(kernel))

# Define agents as plugins
"""

    for agent in blueprint.agents:
        content += f"""
# {agent.name} agent
{agent.name.lower()}_prompt = \"\"\"{agent.role}\"\"\"

@kernel.function(name="{agent.name}")
def {agent.name.lower()}(input_text: str) -> str:
    \"\"\"Agent: {agent.name} - {agent.role}\"\"\"
    return kernel.invoke_plugin_function(
        plugin_name="TextPlugin",
        function_name="summarize",
        variables=sk.ContextVariables(input=input_text, context="{agent.name.lower()}_prompt"),
    )
"""

    content += """

def run_agents():
    \"\"\"Run all agents in sequence or parallel.\"\"\"
    input_data = "Task to be processed"

    # Invoke agents
    results = {{}}
"""

    for agent in blueprint.agents:
        content += f"""    results["{agent.name}"] = {agent.name.lower()}(input_data)
"""

    content += """    return results

if __name__ == "__main__":
    results = run_agents()
    for agent_name, result in results.items():
        print(f"{agent_name}: {result}")
"""

    (out_dir / "agents.py").write_text(content, encoding="utf-8")
    console.print("  [green]✓[/] agents.py — Semantic Kernel agent definitions")

    # Requirements
    reqs = "semantic-kernel>=1.0\nPython-dotenv>=1.0\n"
    (out_dir / "requirements.txt").write_text(reqs, encoding="utf-8")
    console.print("  [green]✓[/] requirements.txt")


def _scaffold_llamaindex(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate LlamaIndex Workflows scaffold."""
    out_dir.mkdir(parents=True, exist_ok=True)

    content = f"""# Generated by CLean-agents for: {blueprint.name}
# LlamaIndex Workflows scaffold
from llama_index.core.workflow import Workflow, step
from llama_index.core.agent import ReActAgent, Tool
from llama_index.llms.openai import OpenAI
import os

# Initialize LLM
llm = OpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))

# Define tools for agents
tools = [
    Tool(
        name="search",
        description="Search for information",
        fn=lambda query: f"Results for: {{query}}",
    ),
    Tool(
        name="summarize",
        description="Summarize text content",
        fn=lambda text: f"Summary: {{text[:100]}}...",
    ),
]

class AgentWorkflow(Workflow):
    \"\"\"LlamaIndex workflow for multi-agent orchestration.\"\"\"

    @step
    async def initialize(self, query: str) -> dict:
        \"\"\"Initialize workflow with input query.\"\"\"
        return {{"query": query, "agents_completed": []}}

"""

    for agent in blueprint.agents:
        content += f"""
    @step
    async def {agent.name}_step(self, context: dict) -> dict:
        \"\"\"Step for {agent.name}: {agent.role}\"\"\"
        agent = ReActAgent.from_tools(
            tools=tools,
            llm=llm,
            system_prompt="{agent.role}",
        )

        response = await agent.achat(context["query"])
        context["agents_completed"].append("{agent.name}")
        context["{agent.name}_result"] = response
        return context
"""

    content += """

    @step
    async def finalize(self, context: dict) -> dict:
        \"\"\"Aggregate results from all agents.\"\"\"
        return {{
            "status": "completed",
            "agents_run": context["agents_completed"],
            "results": {{k: v for k, v in context.items() if k.endswith("_result")}},
        }}


async def run_workflow(query: str):
    \"\"\"Run the agent workflow.\"\"\"
    workflow = AgentWorkflow(timeout=300)
    result = await workflow.run(query=query)
    return result


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(run_workflow("Process this task"))
    print(result)
"""

    (out_dir / "workflow.py").write_text(content, encoding="utf-8")
    console.print("  [green]✓[/] workflow.py — LlamaIndex workflow definition")

    # Requirements
    reqs = "llama-index>=0.11\nllama-index-llms-openai>=0.1\nPython-dotenv>=1.0\n"
    (out_dir / "requirements.txt").write_text(reqs, encoding="utf-8")
    console.print("  [green]✓[/] requirements.txt")


def _scaffold_docker(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate Docker infrastructure."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Dockerfile
    dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "main.py"]
"""
    (out_dir / "Dockerfile").write_text(dockerfile, encoding="utf-8")
    console.print("  [green]✓[/] Dockerfile — Container image definition")

    # Docker Compose
    services = []
    for agent in blueprint.agents:
        services.append(f"""  {agent.name}:
    build: .
    environment:
      - AGENT_NAME={agent.name}
      - OPENAI_API_KEY=${{OPENAI_API_KEY}}
      - LOG_LEVEL=info
    depends_on:
      - redis
      - postgres
    networks:
      - agent-network
    restart: unless-stopped
""")

    docker_compose = f"""version: '3.8'

services:
{chr(10).join(services)}
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - agent-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: agent_user
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:-changeme}}
      POSTGRES_DB: agents_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - agent-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agent_user"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:

networks:
  agent-network:
    driver: bridge
"""
    (out_dir / "docker-compose.yml").write_text(docker_compose, encoding="utf-8")
    console.print("  [green]✓[/] docker-compose.yml — Multi-container orchestration")

    # .env.example
    env_example = """# API Keys and Credentials
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration
POSTGRES_USER=agent_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=agents_db

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Logging and Debug
LOG_LEVEL=info
DEBUG=false

# Agent Configuration
AGENT_TIMEOUT=300
MAX_RETRIES=3

# Vector Database (optional)
# WEAVIATE_URL=http://weaviate:8080
# PINECONE_API_KEY=your_pinecone_key_here
"""
    (out_dir / ".env.example").write_text(env_example, encoding="utf-8")
    console.print("  [green]✓[/] .env.example — Environment variables template")

    # .dockerignore
    dockerignore = """__pycache__
*.pyc
.pytest_cache
.git
.gitignore
.env
*.log
.DS_Store
node_modules
dist
build
.venv
venv
"""
    (out_dir / ".dockerignore").write_text(dockerignore, encoding="utf-8")
    console.print("  [green]✓[/] .dockerignore — Docker build exclusions")


def _scaffold_terraform(blueprint: Blueprint, out_dir: Path) -> None:
    """Generate Terraform infrastructure (AWS ECS/Fargate)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tf_dir = out_dir / "terraform"
    tf_dir.mkdir(exist_ok=True)

    # main.tf
    main_tf = f"""# Generated Terraform configuration for {blueprint.name}
terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
}}

# ECS Cluster
resource "aws_ecs_cluster" "agents_cluster" {{
  name = "${{var.project_name}}-cluster"

  setting {{
    name  = "containerInsights"
    value = "enabled"
  }}

  tags = {{
    Name        = "${{var.project_name}}-cluster"
    Environment = var.environment
  }}
}}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "agents_logs" {{
  name              = "/ecs/${{var.project_name}}"
  retention_in_days = var.log_retention_days

  tags = {{
    Name = "${{var.project_name}}-logs"
  }}
}}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {{
  name = "${{var.project_name}}-ecs-task-execution-role"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{
        Service = "ecs-tasks.amazonaws.com"
      }}
    }}]
  }})
}}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {{
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task_role" {{
  name = "${{var.project_name}}-ecs-task-role"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{
        Service = "ecs-tasks.amazonaws.com"
      }}
    }}]
  }})
}}

# ECS Task Definition
resource "aws_ecs_task_definition" "agents_task" {{
  family                   = var.project_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
"""

    for idx, agent in enumerate(blueprint.agents):
        main_tf += f"""    {{
      name      = "{agent.name}"
      image     = "${{var.ecr_repository_url}}:{agent.name}-${{var.image_tag}}"
      essential = {str(idx == 0).lower()}

      portMappings = [{{
        containerPort = 8000
        hostPort      = 8000
        protocol      = "tcp"
      }}]

      logConfiguration = {{
        logDriver = "awslogs"
        options = {{
          "awslogs-group"         = aws_cloudwatch_log_group.agents_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "{agent.name}"
        }}
      }}

      environment = [
        {{
          name  = "AGENT_NAME"
          value = "{agent.name}"
        }},
        {{
          name  = "LOG_LEVEL"
          value = var.log_level
        }}
      ]

      secrets = [
        {{
          name      = "OPENAI_API_KEY"
          valueFrom = "${{aws_secretsmanager_secret.openai_api_key.arn}}"
        }}
      ]
    }},
"""

    main_tf += """  ])

  tags = {
    Name = var.project_name
  }
}

# ECS Service
resource "aws_ecs_service" "agents_service" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.agents_cluster.id
  task_definition = aws_ecs_task_definition.agents_task.arn
  desired_count   = var.desired_task_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = var.assign_public_ip
  }

  tags = {
    Name = "${var.project_name}-service"
  }

  depends_on = [aws_ec2_network_interface.ecs_service]
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-ecs-tasks"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ecs-tasks"
  }
}

# Network Interface (placeholder - adjust as needed)
resource "aws_ec2_network_interface" "ecs_service" {
  subnet_id = var.subnet_ids[0]

  tags = {
    Name = "${var.project_name}-ecs-eni"
  }
}

# Secrets Manager for API Keys
resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${var.project_name}/openai-api-key"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-openai-api-key"
  }
}

resource "aws_secretsmanager_secret_version" "openai_api_key_version" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}
"""
    (tf_dir / "main.tf").write_text(main_tf, encoding="utf-8")
    console.print("  [green]✓[/] terraform/main.tf — ECS/Fargate infrastructure")

    # variables.tf
    variables_tf = """variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
}

variable "task_cpu" {
  description = "Task CPU units (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Task memory in MB (512, 1024, 2048, 3072, 4096, 5120, 6144, 7168, 8192)"
  type        = number
  default     = 1024
}

variable "desired_task_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 2
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "ecr_repository_url" {
  description = "ECR repository URL"
  type        = string
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "info"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "assign_public_ip" {
  description = "Assign public IP to tasks"
  type        = bool
  default     = false
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access tasks"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}
"""
    (tf_dir / "variables.tf").write_text(variables_tf, encoding="utf-8")
    console.print("  [green]✓[/] terraform/variables.tf — Configurable variables")

    # outputs.tf
    outputs_tf = """output "ecs_cluster_name" {
  description = "ECS Cluster name"
  value       = aws_ecs_cluster.agents_cluster.name
}

output "ecs_service_name" {
  description = "ECS Service name"
  value       = aws_ecs_service.agents_service.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group name"
  value       = aws_cloudwatch_log_group.agents_logs.name
}

output "iam_task_execution_role_arn" {
  description = "IAM Task Execution Role ARN"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "iam_task_role_arn" {
  description = "IAM Task Role ARN"
  value       = aws_iam_role.ecs_task_role.arn
}

output "security_group_id" {
  description = "Security Group ID"
  value       = aws_security_group.ecs_tasks.id
}

output "secrets_manager_secret_arn" {
  description = "Secrets Manager Secret ARN"
  value       = aws_secretsmanager_secret.openai_api_key.arn
}
"""
    (tf_dir / "outputs.tf").write_text(outputs_tf, encoding="utf-8")
    console.print("  [green]✓[/] terraform/outputs.tf — Service outputs")

    # terraform.tfvars.example
    tfvars_example = """# AWS Configuration
aws_region = "us-east-1"

# Project Configuration
project_name = "clean-agents-system"
environment  = "dev"

# VPC Configuration - UPDATE WITH YOUR VALUES
vpc_id    = "vpc-xxxxxxxxx"
subnet_ids = [
  "subnet-xxxxxxxxx",
  "subnet-yyyyyyyyy"
]

# ECS Task Configuration
task_cpu    = 512
task_memory = 1024

# Scaling
desired_task_count = 2

# ECR Configuration
ecr_repository_url = "123456789.dkr.ecr.us-east-1.amazonaws.com/clean-agents"
image_tag          = "latest"

# Logging
log_level          = "info"
log_retention_days = 30

# Network
assign_public_ip      = false
allowed_cidr_blocks   = ["0.0.0.0/0"]

# Secrets - UPDATE WITH YOUR VALUES
openai_api_key = "sk-..."
"""
    (tf_dir / "terraform.tfvars.example").write_text(tfvars_example, encoding="utf-8")
    console.print("  [green]✓[/] terraform/terraform.tfvars.example — Terraform variables")

    console.print("  [green]✓[/] Terraform infrastructure scaffolding complete")
