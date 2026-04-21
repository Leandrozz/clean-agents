"""Tests for the benchmark harness module."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from clean_agents.core.agent import AgentSpec, ModelConfig
from clean_agents.core.blueprint import ArchitecturePattern, Blueprint, SystemType
from clean_agents.harness.benchmark import (
    BenchmarkRunner,
    BenchmarkSuite,
    BenchmarkTask,
    TaskResult,
)
from clean_agents.harness.providers import MockProvider
from clean_agents.harness.runtime import HarnessResult, TokenUsage


@pytest.fixture
def simple_blueprint() -> Blueprint:
    """Create a simple test blueprint."""
    return Blueprint(
        name="test-blueprint",
        system_type=SystemType.SINGLE_AGENT,
        pattern=ArchitecturePattern.SINGLE,
        agents=[
            AgentSpec(
                name="worker",
                role="Process requests",
                model=ModelConfig(primary="claude-sonnet-4-6"),
            ),
        ],
    )


@pytest.fixture
def multi_agent_blueprint() -> Blueprint:
    """Create a multi-agent test blueprint."""
    return Blueprint(
        name="multi-agent-blueprint",
        system_type=SystemType.MULTI_AGENT,
        pattern=ArchitecturePattern.SUPERVISOR_HIERARCHICAL,
        agents=[
            AgentSpec(
                name="supervisor",
                role="Coordinate tasks",
                agent_type="orchestrator",
                model=ModelConfig(primary="claude-sonnet-4-6"),
            ),
            AgentSpec(
                name="analyst",
                role="Analyze data",
                model=ModelConfig(primary="claude-haiku-4-5"),
            ),
        ],
    )


@pytest.fixture
def benchmark_suite() -> BenchmarkSuite:
    """Create a test benchmark suite."""
    return BenchmarkSuite(
        name="test-suite",
        description="Test benchmark suite",
        tasks=[
            BenchmarkTask(
                name="task1",
                input_message="Hello",
                expected_keywords=["response"],
                category="greeting",
            ),
            BenchmarkTask(
                name="task2",
                input_message="Calculate 2 + 2",
                expected_keywords=["4"],
                category="math",
            ),
            BenchmarkTask(
                name="task3",
                input_message="What is AI?",
                expected_output="artificial intelligence",
                category="knowledge",
            ),
        ],
    )


class TestBenchmarkTask:
    """Tests for BenchmarkTask model."""

    def test_task_defaults(self) -> None:
        """Test BenchmarkTask default values."""
        task = BenchmarkTask(
            name="test",
            input_message="Test input",
        )
        assert task.name == "test"
        assert task.input_message == "Test input"
        assert task.expected_output is None
        assert task.expected_keywords == []
        assert task.category == "general"
        assert task.max_rounds == 10
        assert task.timeout_seconds == 30.0

    def test_task_with_keywords(self) -> None:
        """Test BenchmarkTask with expected keywords."""
        task = BenchmarkTask(
            name="test",
            input_message="Test",
            expected_keywords=["foo", "bar"],
        )
        assert task.expected_keywords == ["foo", "bar"]


class TestBenchmarkSuite:
    """Tests for BenchmarkSuite model."""

    def test_default_suite_has_tasks(self) -> None:
        """Test that default suite includes diverse tasks."""
        suite = BenchmarkSuite.default_suite()
        assert suite.name == "default"
        assert len(suite.tasks) >= 8
        assert all(task.name for task in suite.tasks)
        # Note: Some tasks may have empty input (like edge_case_empty), so check most have content
        assert sum(1 for task in suite.tasks if task.input_message) >= 8

    def test_default_suite_has_categories(self) -> None:
        """Test that default suite covers multiple categories."""
        suite = BenchmarkSuite.default_suite()
        categories = {task.category for task in suite.tasks}
        expected_categories = {
            "classification",
            "reasoning",
            "tool-use",
            "safety",
            "medical",
            "legal",
            "edge-case",
            "ambiguous",
            "context",
        }
        assert expected_categories.issubset(categories)

    def test_suite_save_load_yaml(self) -> None:
        """Test saving and loading benchmark suite from YAML."""
        suite = BenchmarkSuite(
            name="test",
            description="Test suite",
            tasks=[
                BenchmarkTask(
                    name="task1",
                    input_message="Input 1",
                    expected_keywords=["keyword1"],
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "suite.yaml"
            suite.save(path)
            assert path.exists()

            loaded = BenchmarkSuite.from_yaml(path)
            assert loaded.name == "test"
            assert len(loaded.tasks) == 1
            assert loaded.tasks[0].name == "task1"


class TestBenchmarkRunner:
    """Tests for BenchmarkRunner."""

    @pytest.mark.asyncio
    async def test_benchmark_single_blueprint(
        self,
        simple_blueprint: Blueprint,
        benchmark_suite: BenchmarkSuite,
    ) -> None:
        """Test running benchmark against a single blueprint."""
        runner = BenchmarkRunner()
        score = await runner.run_suite(simple_blueprint, benchmark_suite)

        assert score.blueprint_name == "test-blueprint"
        assert score.total_agents == 1
        assert score.tasks_total == 3
        assert 0.0 <= score.pass_rate <= 1.0
        assert 0.0 <= score.avg_score <= 1.0
        assert len(score.task_results) == 3

    @pytest.mark.asyncio
    async def test_benchmark_comparison(
        self,
        simple_blueprint: Blueprint,
        multi_agent_blueprint: Blueprint,
        benchmark_suite: BenchmarkSuite,
    ) -> None:
        """Test comparing multiple blueprints."""
        runner = BenchmarkRunner()
        comparison = await runner.compare(
            [simple_blueprint, multi_agent_blueprint],
            benchmark_suite,
        )

        assert comparison.suite_name == "test-suite"
        assert len(comparison.scores) == 2
        assert comparison.winner in [simple_blueprint.name, multi_agent_blueprint.name]
        assert "Best performing" in comparison.summary

    @pytest.mark.asyncio
    async def test_score_exact_match(self, simple_blueprint: Blueprint) -> None:
        """Test scoring with exact expected output."""
        runner = BenchmarkRunner()
        task = BenchmarkTask(
            name="exact_match",
            input_message="Test",
            expected_output="exact response",
        )
        result = HarnessResult(
            final_output="This is an exact response here.",
            agent_traces=[],
        )

        score = runner._score_result(task, result)
        assert score > 0.5  # Should score higher with expected output

    @pytest.mark.asyncio
    async def test_score_keyword_match(self, simple_blueprint: Blueprint) -> None:
        """Test scoring with keyword matching."""
        runner = BenchmarkRunner()
        task = BenchmarkTask(
            name="keyword_match",
            input_message="Test",
            expected_keywords=["foo", "bar"],
        )
        result = HarnessResult(
            final_output="This contains foo and bar keywords.",
            agent_traces=[],
        )

        score = runner._score_result(task, result)
        assert score > 0.5  # Should score higher with keywords

    @pytest.mark.asyncio
    async def test_score_with_errors(self, simple_blueprint: Blueprint) -> None:
        """Test scoring with errors returns zero."""
        runner = BenchmarkRunner()
        task = BenchmarkTask(
            name="error_case",
            input_message="Test",
        )
        result = HarnessResult(
            final_output="",
            errors=["Agent failed"],
        )

        score = runner._score_result(task, result)
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_category_scores(self, benchmark_suite: BenchmarkSuite) -> None:
        """Test that category scores are computed."""
        simple_blueprint = Blueprint(
            name="test",
            system_type=SystemType.SINGLE_AGENT,
            pattern=ArchitecturePattern.SINGLE,
            agents=[
                AgentSpec(
                    name="worker",
                    role="Test",
                    model=ModelConfig(primary="claude-sonnet-4-6"),
                ),
            ],
        )

        runner = BenchmarkRunner()
        score = await runner.run_suite(simple_blueprint, benchmark_suite)

        assert len(score.category_scores) > 0
        for category, cat_score in score.category_scores.items():
            assert 0.0 <= cat_score <= 1.0

    @pytest.mark.asyncio
    async def test_benchmark_with_timeout(self) -> None:
        """Test that tasks timeout correctly."""
        blueprint = Blueprint(
            name="test",
            system_type=SystemType.SINGLE_AGENT,
            pattern=ArchitecturePattern.SINGLE,
            agents=[
                AgentSpec(
                    name="worker",
                    role="Test",
                    model=ModelConfig(primary="claude-sonnet-4-6"),
                ),
            ],
        )

        suite = BenchmarkSuite(
            name="timeout-test",
            tasks=[
                BenchmarkTask(
                    name="timeout-task",
                    input_message="Test",
                    timeout_seconds=0.001,  # Very short timeout
                ),
            ],
        )

        runner = BenchmarkRunner()
        score = await runner.run_suite(blueprint, suite)

        # Task should have been recorded even if it timed out
        assert len(score.task_results) == 1
        assert "timeout" in score.task_results[0].error.lower()


class TestTaskResult:
    """Tests for TaskResult model."""

    def test_task_result_passed(self) -> None:
        """Test TaskResult with passed task."""
        result = TaskResult(
            task_name="test",
            blueprint_name="blueprint",
            passed=True,
            score=0.95,
        )
        assert result.passed
        assert result.score == 0.95

    def test_task_result_with_error(self) -> None:
        """Test TaskResult with error."""
        result = TaskResult(
            task_name="test",
            blueprint_name="blueprint",
            passed=False,
            score=0.0,
            error="Agent timeout",
        )
        assert not result.passed
        assert result.error == "Agent timeout"


class TestBlueprintScore:
    """Tests for BlueprintScore model."""

    def test_blueprint_score_computation(self) -> None:
        """Test BlueprintScore aggregation."""
        from clean_agents.harness.benchmark import BlueprintScore

        score = BlueprintScore(
            blueprint_name="test",
            pattern="single",
            total_agents=1,
            tasks_passed=3,
            tasks_total=5,
            pass_rate=0.6,
            avg_score=0.72,
            avg_latency_ms=150.5,
            avg_cost=0.01,
            total_cost=0.05,
            total_tokens=TokenUsage(input_tokens=1000, output_tokens=500),
        )

        assert score.pass_rate == 0.6
        assert score.total_tokens.total == 1500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
