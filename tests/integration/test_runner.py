"""
Integration test runner and reporting system.

This module provides comprehensive test execution, monitoring,
and reporting capabilities for the B2BValue agent system.
"""

import asyncio
import json
import logging
import psutil
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Import pytest for test discovery and execution
import pytest

# Add parent directories to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent))  # Add project root
sys.path.insert(0, str(current_dir.parent))  # Add tests directory

from tests.integration.test_config import (
    IntegrationTestConfig, TestConfigurationManager, TestDataManager,
    TEST_RESULTS_DIR, cleanup_test_environment, create_test_directories
)

from dataclasses import dataclass, asdict
from statistics import mean


@dataclass
class TestResult:
    """Individual test result."""
    test_name: str
    status: str  # passed, failed, skipped, error
    duration_ms: float
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TestSuiteResult:
    """Test suite execution result."""
    suite_name: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    success_rate: float
    test_results: List[TestResult]
    system_metrics: Dict[str, Any]
    configuration: Dict[str, Any]
    
    @property
    def status(self) -> str:
        """Overall suite status."""
        if self.errors > 0:
            return "error"
        elif self.failed > 0:
            return "failed"
        elif self.skipped == self.total_tests:
            return "skipped"
        else:
            return "passed"


@dataclass
class TestExecutionReport:
    """Comprehensive test execution report."""
    execution_id: str
    start_time: datetime
    end_time: datetime
    total_duration_ms: float
    environment: str
    configuration: Dict[str, Any]
    suite_results: List[TestSuiteResult]
    summary: Dict[str, Any]
    recommendations: List[str]
    
    @property
    def overall_status(self) -> str:
        """Overall execution status."""
        if any(suite.status == "error" for suite in self.suite_results):
            return "error"
        elif any(suite.status == "failed" for suite in self.suite_results):
            return "failed"
        else:
            return "passed"
    
    @property
    def total_tests(self) -> int:
        """Total number of tests executed."""
        return sum(suite.total_tests for suite in self.suite_results)
    
    @property
    def total_passed(self) -> int:
        """Total number of tests passed."""
        return sum(suite.passed for suite in self.suite_results)
    
    @property
    def total_failed(self) -> int:
        """Total number of tests failed."""
        return sum(suite.failed for suite in self.suite_results)
    
    @property
    def total_errors(self) -> int:
        """Total number of test errors."""
        return sum(suite.errors for suite in self.suite_results)
    
    @property
    def overall_success_rate(self) -> float:
        """Overall success rate across all tests."""
        if self.total_tests == 0:
            return 0.0
        return self.total_passed / self.total_tests


class SystemMonitor:
    """System resource monitoring during test execution."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.metrics = []
    
    def start_monitoring(self):
        """Start system monitoring."""
        self.monitoring = True
        self.metrics = []
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        try:
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
            
            # Get system-wide metrics
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=0.1)
            
            metrics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "process_memory_mb": memory_info.rss / 1024 / 1024,
                "process_cpu_percent": cpu_percent,
                "system_memory_percent": system_memory.percent,
                "system_cpu_percent": system_cpu,
                "system_memory_available_mb": system_memory.available / 1024 / 1024
            }
            
            if self.monitoring:
                self.metrics.append(metrics)
            
            return metrics
        except Exception as e:
            logging.warning(f"Failed to collect system metrics: {e}")
            return {}
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        if not self.metrics:
            return {}
        
        memory_values = [m.get("process_memory_mb", 0) for m in self.metrics]
        cpu_values = [m.get("process_cpu_percent", 0) for m in self.metrics]
        
        return {
            "memory_usage": {
                "avg_mb": mean(memory_values),
                "max_mb": max(memory_values),
                "min_mb": min(memory_values)
            },
            "cpu_usage": {
                "avg_percent": mean(cpu_values),
                "max_percent": max(cpu_values),
                "min_percent": min(cpu_values)
            },
            "sample_count": len(self.metrics)
        }


class TestRunner:
    """Main test runner for integration tests."""
    
    def __init__(self, config: IntegrationTestConfig):
        self.config = config
        self.system_monitor = SystemMonitor()
        self.logger = self._setup_logging()
        self.execution_id = self._generate_execution_id()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for test execution."""
        logger = logging.getLogger("integration_test_runner")
        logger.setLevel(logging.INFO)
        
        # Create log file handler
        log_file = TEST_RESULTS_DIR / f"test_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _generate_execution_id(self) -> str:
        """Generate unique execution ID."""
        return f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def run_all_tests(self) -> TestExecutionReport:
        """Run all integration tests and generate comprehensive report."""
        self.logger.info(f"Starting integration test execution: {self.execution_id}")
        start_time = datetime.now(timezone.utc)
        
        # Start system monitoring
        self.system_monitor.start_monitoring()
        
        suite_results = []
        
        try:
            # Run each test suite
            test_suites = [
                ("business_case_workflow", "test_business_case_workflow.py"),
                ("mcp_compliance", "test_mcp_compliance.py"),
                ("load_performance", "test_load_performance.py")
            ]
            
            for suite_name, test_file in test_suites:
                self.logger.info(f"Running test suite: {suite_name}")
                suite_result = await self._run_test_suite(suite_name, test_file)
                suite_results.append(suite_result)
                
                # Log suite completion
                self.logger.info(
                    f"Completed {suite_name}: {suite_result.passed}/{suite_result.total_tests} passed "
                    f"({suite_result.success_rate:.1%} success rate)"
                )
        
        except Exception as e:
            self.logger.error(f"Error during test execution: {e}")
            self.logger.error(traceback.format_exc())
        
        finally:
            # Stop system monitoring
            self.system_monitor.stop_monitoring()
        
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - start_time).total_seconds() * 1000
        
        # Generate comprehensive report
        report = TestExecutionReport(
            execution_id=self.execution_id,
            start_time=start_time,
            end_time=end_time,
            total_duration_ms=total_duration,
            environment=self.config.test_environment,
            configuration=asdict(self.config),
            suite_results=suite_results,
            summary=self._generate_summary(suite_results),
            recommendations=self._generate_recommendations(suite_results)
        )
        
        # Save report
        await self._save_report(report)
        
        self.logger.info(f"Integration test execution completed: {report.overall_status}")
        self.logger.info(
            f"Total: {report.total_tests} tests, {report.total_passed} passed, "
            f"{report.total_failed} failed, {report.total_errors} errors "
            f"({report.overall_success_rate:.1%} success rate)"
        )
        
        return report
    
    async def _run_test_suite(self, suite_name: str, test_file: str) -> TestSuiteResult:
        """Run a specific test suite."""
        start_time = datetime.now(timezone.utc)
        test_results = []
        
        try:
            # Run pytest with JSON reporting
            test_file_path = Path(__file__).parent / test_file
            result_file = TEST_RESULTS_DIR / f"{suite_name}_results.json"
            
            cmd = [
                sys.executable, "-m", "pytest",
                str(test_file_path),
                f"--json-report",
                f"--json-report-file={result_file}",
                "--tb=short",
                "-v"
            ]
            
            # Run pytest subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path(__file__).parent
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse results
            if result_file.exists():
                with open(result_file, 'r') as f:
                    pytest_results = json.load(f)
                
                test_results = self._parse_pytest_results(pytest_results)
            else:
                self.logger.warning(f"No results file found for {suite_name}")
        
        except Exception as e:
            self.logger.error(f"Error running test suite {suite_name}: {e}")
            test_results = [TestResult(
                test_name=f"{suite_name}_execution_error",
                status="error",
                duration_ms=0,
                error_message=str(e),
                error_traceback=traceback.format_exc()
            )]
        
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Calculate statistics
        total_tests = len(test_results)
        passed = sum(1 for r in test_results if r.status == "passed")
        failed = sum(1 for r in test_results if r.status == "failed")
        skipped = sum(1 for r in test_results if r.status == "skipped")
        errors = sum(1 for r in test_results if r.status == "error")
        success_rate = passed / total_tests if total_tests > 0 else 0.0
        
        return TestSuiteResult(
            suite_name=suite_name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            success_rate=success_rate,
            test_results=test_results,
            system_metrics=self.system_monitor.get_summary_metrics(),
            configuration=asdict(self.config)
        )
    
    def _parse_pytest_results(self, pytest_results: Dict[str, Any]) -> List[TestResult]:
        """Parse pytest JSON results into TestResult objects."""
        test_results = []
        
        tests = pytest_results.get("tests", [])
        
        for test in tests:
            # Extract test information
            test_name = test.get("nodeid", "unknown")
            outcome = test.get("outcome", "unknown")
            duration = test.get("duration", 0) * 1000  # Convert to milliseconds
            
            # Map pytest outcomes to our status
            status_mapping = {
                "passed": "passed",
                "failed": "failed",
                "skipped": "skipped",
                "error": "error"
            }
            status = status_mapping.get(outcome, "error")
            
            # Extract error information
            error_message = None
            error_traceback = None
            
            if status in ["failed", "error"]:
                call_info = test.get("call", {})
                error_message = call_info.get("longrepr", "Unknown error")
                error_traceback = call_info.get("crash", {}).get("traceback", "")
            
            test_results.append(TestResult(
                test_name=test_name,
                status=status,
                duration_ms=duration,
                error_message=error_message,
                error_traceback=error_traceback,
                metadata={"outcome": outcome}
            ))
        
        return test_results
    
    def _generate_summary(self, suite_results: List[TestSuiteResult]) -> Dict[str, Any]:
        """Generate execution summary."""
        if not suite_results:
            return {}
        
        # Calculate overall metrics
        total_duration = sum(suite.duration_ms for suite in suite_results)
        avg_duration = total_duration / len(suite_results)
        
        # Performance metrics
        durations = [suite.duration_ms for suite in suite_results]
        
        # Success rate by suite
        suite_success_rates = {
            suite.suite_name: suite.success_rate
            for suite in suite_results
        }
        
        return {
            "execution_metrics": {
                "total_duration_ms": total_duration,
                "average_suite_duration_ms": avg_duration,
                "longest_suite_duration_ms": max(durations),
                "shortest_suite_duration_ms": min(durations)
            },
            "success_metrics": {
                "suite_success_rates": suite_success_rates,
                "average_success_rate": mean(suite_success_rates.values()),
                "lowest_success_rate": min(suite_success_rates.values()),
                "highest_success_rate": max(suite_success_rates.values())
            },
            "system_metrics": self.system_monitor.get_summary_metrics(),
            "test_distribution": {
                suite.suite_name: {
                    "total": suite.total_tests,
                    "passed": suite.passed,
                    "failed": suite.failed,
                    "errors": suite.errors,
                    "skipped": suite.skipped
                }
                for suite in suite_results
            }
        }
    
    def _generate_recommendations(self, suite_results: List[TestSuiteResult]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Overall success rate recommendations
        overall_success_rate = sum(suite.success_rate for suite in suite_results) / len(suite_results)
        
        if overall_success_rate < 0.8:
            recommendations.append(
                "Overall success rate is below 80%. Consider reviewing failed tests and addressing "
                "underlying issues before production deployment."
            )
        elif overall_success_rate < 0.95:
            recommendations.append(
                "Success rate is acceptable but could be improved. Review failed tests for optimization opportunities."
            )
        
        # Performance recommendations
        slow_suites = [suite for suite in suite_results if suite.duration_ms > 30000]
        if slow_suites:
            slow_names = [suite.suite_name for suite in slow_suites]
            recommendations.append(
                f"The following test suites are running slowly (>30s): {', '.join(slow_names)}. "
                "Consider optimizing test execution or reviewing timeout configurations."
            )
        
        # Error rate recommendations
        error_suites = [suite for suite in suite_results if suite.errors > 0]
        if error_suites:
            error_names = [suite.suite_name for suite in error_suites]
            recommendations.append(
                f"Test suites with errors detected: {', '.join(error_names)}. "
                "Review error logs and fix issues before deployment."
            )
        
        # Memory usage recommendations
        system_metrics = self.system_monitor.get_summary_metrics()
        if system_metrics and system_metrics.get("memory_usage", {}).get("max_mb", 0) > 512:
            recommendations.append(
                "High memory usage detected during testing. Monitor memory consumption in production "
                "and consider implementing memory optimization strategies."
            )
        
        # Suite-specific recommendations
        for suite in suite_results:
            if suite.success_rate < 0.9 and suite.total_tests > 5:
                recommendations.append(
                    f"Test suite '{suite.suite_name}' has low success rate ({suite.success_rate:.1%}). "
                    "Review individual test failures and address root causes."
                )
        
        if not recommendations:
            recommendations.append(
                "All tests are performing well. The system appears ready for production deployment."
            )
        
        return recommendations
    
    async def _save_report(self, report: TestExecutionReport):
        """Save test execution report."""
        # Save JSON report
        json_file = TEST_RESULTS_DIR / f"{report.execution_id}_report.json"
        with open(json_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        
        # Save HTML report
        html_file = TEST_RESULTS_DIR / f"{report.execution_id}_report.html"
        html_content = self._generate_html_report(report)
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        self.logger.info(f"Test report saved: {json_file}")
        self.logger.info(f"HTML report saved: {html_file}")
    
    def _generate_html_report(self, report: TestExecutionReport) -> str:
        """Generate HTML report."""
        # Simple HTML template for the report
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Integration Test Report - {report.execution_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .suite {{ margin: 20px 0; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .error {{ color: orange; }}
        .skipped {{ color: gray; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .recommendations {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Integration Test Report</h1>
        <p><strong>Execution ID:</strong> {report.execution_id}</p>
        <p><strong>Status:</strong> <span class="{report.overall_status}">{report.overall_status.upper()}</span></p>
        <p><strong>Duration:</strong> {report.total_duration_ms/1000:.2f} seconds</p>
        <p><strong>Success Rate:</strong> {report.overall_success_rate:.1%}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Tests</td>
                <td>{report.total_tests}</td>
            </tr>
            <tr>
                <td class="passed">Passed</td>
                <td>{report.total_passed}</td>
            </tr>
            <tr>
                <td class="failed">Failed</td>
                <td>{report.total_failed}</td>
            </tr>
            <tr>
                <td class="error">Errors</td>
                <td>{report.total_errors}</td>
            </tr>
        </table>
    </div>
    
    <div class="suites">
        <h2>Test Suites</h2>
        {"".join(self._generate_suite_html(suite) for suite in report.suite_results)}
    </div>
    
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
            {"".join(f"<li>{rec}</li>" for rec in report.recommendations)}
        </ul>
    </div>
</body>
</html>
        """
        return html_template
    
    def _generate_suite_html(self, suite: TestSuiteResult) -> str:
        """Generate HTML for a test suite."""
        return f"""
        <div class="suite">
            <h3>{suite.suite_name}</h3>
            <p><strong>Status:</strong> <span class="{suite.status}">{suite.status.upper()}</span></p>
            <p><strong>Duration:</strong> {suite.duration_ms/1000:.2f} seconds</p>
            <p><strong>Success Rate:</strong> {suite.success_rate:.1%}</p>
            <p><strong>Tests:</strong> {suite.total_tests} total, {suite.passed} passed, {suite.failed} failed, {suite.errors} errors</p>
        </div>
        """


async def main():
    """Main entry point for test runner."""
    # Load configuration
    config = TestConfigurationManager.load_config()
    
    # Initialize test environment
    create_test_directories()
    
    # Create and run test runner
    runner = TestRunner(config)
    report = await runner.run_all_tests()
    
    # Print summary
    print("\n" + "="*80)
    print("INTEGRATION TEST EXECUTION SUMMARY")
    print("="*80)
    print(f"Execution ID: {report.execution_id}")
    print(f"Overall Status: {report.overall_status.upper()}")
    print(f"Total Duration: {report.total_duration_ms/1000:.2f} seconds")
    print(f"Success Rate: {report.overall_success_rate:.1%}")
    print(f"Tests: {report.total_tests} total, {report.total_passed} passed, {report.total_failed} failed")
    print("\nRecommendations:")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"{i}. {rec}")
    print("="*80)
    
    # Cleanup
    cleanup_test_environment()
    
    # Exit with appropriate code
    sys.exit(0 if report.overall_status == "passed" else 1)


if __name__ == "__main__":
    asyncio.run(main())
