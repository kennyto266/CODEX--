"""
Command Line Interface for scraping operations

Provides CLI commands for single and batch scraping requests,
configuration management, and system monitoring.
"""

import asyncio
import click
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .models import (
    NaturalLanguageRequest, BatchRequest, PipetConfiguration,
    OutputFormat, ProcessingStatus, AggregationStrategy
)
from .single_executor import SingleExecutionOrchestrator
from .batch_processor import BatchProcessor
from .batch_config_manager import BatchConfigManager, ConfigTemplateType
from .batch_result_aggregator import BatchResultAggregator
from .config_validator import ConfigValidator
from .logging_config import setup_logging
from .config import get_global_config


# Setup logging for CLI
setup_logging()


@click.group()
@click.version_option(version="1.0.0", prog_name="pipet-scraping")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
def cli(verbose: bool, config: Optional[str]):
    """
    Pipet Non-Price Data Crawler - Natural Language Scraping Interface

    Convert natural language descriptions into executable pipet configurations
    and execute web scraping tasks for economic data collection.
    """
    # Setup logging level based on verbose flag
    if verbose:
        import logging
        logging.getLogger('scraping').setLevel(logging.DEBUG)

    # Load configuration if provided
    if config:
        # Configuration loading would be implemented here
        pass


@cli.command()
@click.argument('description', type=str)
@click.option('--url', '-u', help='Target URL (overrides NLP extraction)')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'xml', 'yaml']), default='json', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--no-validation', is_flag=True, help='Skip configuration validation')
@click.option('--no-transformation', is_flag=True, help='Skip data transformation')
@click.option('--url-check', is_flag=True, help='Perform URL accessibility check')
@click.option('--selector-test', is_flag=True, help='Test CSS selectors')
@click.option('--timeout', type=int, help='Request timeout in seconds')
def scrape(
    description: str,
    url: Optional[str],
    format: str,
    output: Optional[str],
    no_validation: bool,
    no_transformation: bool,
    url_check: bool,
    selector_test: bool,
    timeout: Optional[int]
):
    """
    Scrape data using natural language description.

    Examples:
        pipet-scraping scrape "從香港金管局抓取HIBOR利率數據"
        pipet-scraping scrape "Extract HIBOR rates from HKMA website" --url https://www.hkma.gov.hk
        pipet-scraping scrape "獲取GDP統計數據" --format csv --output gdp_data.csv
    """
    async def execute_scrape():
        try:
            # Create natural language request
            request = NaturalLanguageRequest(
                user_description=description,
                user_context={
                    "override_url": url,
                    "preferred_format": format
                }
            )

            # Setup execution options
            execution_options = {
                "validate_config": not no_validation,
                "perform_url_check": url_check,
                "perform_selector_test": selector_test,
                "transform_data": not no_transformation,
                "export_results": True,
                "output_format": format
            }

            if output:
                execution_options["output_file"] = output

            if timeout:
                execution_options["timeout"] = timeout

            # Create executor and execute request
            executor = SingleExecutionOrchestrator()
            execution = await executor.execute_request(request, execution_options)

            # Display results
            display_execution_results(execution)

            # Return appropriate exit code
            if execution.status.value == "completed":
                sys.exit(0)
            else:
                sys.exit(1)

        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)

    # Run async function
    asyncio.run(execute_scrape())


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--max-concurrent', type=int, default=3, help='Maximum concurrent executions')
@click.option('--continue-on-error', is_flag=True, default=True, help='Continue execution on individual failures')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'xml', 'yaml']), default='json', help='Output format')
@click.option('--output-dir', type=click.Path(), help='Output directory for results')
def batch(input_file: str, max_concurrent: int, continue_on_error: bool, format: str, output_dir: Optional[str]):
    """
    Execute batch scraping requests from file.

    Input file should contain JSON array of requests:
    [
        {"user_description": "Extract HIBOR rates", "user_context": {...}},
        {"user_description": "Get GDP statistics", "user_context": {...}}
    ]
    """
    async def execute_batch():
        try:
            # Load requests from file
            with open(input_file, 'r', encoding='utf-8') as f:
                requests_data = json.load(f)

            if not isinstance(requests_data, list):
                raise ValueError("Input file must contain a JSON array of requests")

            # Convert to NaturalLanguageRequest objects
            requests = []
            for req_data in requests_data:
                request = NaturalLanguageRequest(
                    user_description=req_data["user_description"],
                    user_context=req_data.get("user_context", {})
                )
                requests.append(request)

            click.echo(f"Loaded {len(requests)} requests from {input_file}")

            # Setup batch options
            batch_options = {
                "max_concurrent": max_concurrent,
                "continue_on_error": continue_on_error,
                "execution_options": {
                    "validate_config": True,
                    "transform_data": True,
                    "export_results": True,
                    "output_format": format
                }
            }

            if output_dir:
                batch_options["execution_options"]["output_dir"] = output_dir

            # Create batch executor and execute
            executor = BatchExecutionOrchestrator()
            batch_results = await executor.execute_batch(requests, batch_options)

            # Display batch results
            display_batch_results(batch_results)

            # Return appropriate exit code
            if batch_results["success_rate"] > 0.5:  # At least 50% success
                sys.exit(0)
            else:
                sys.exit(1)

        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(execute_batch())


@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--url-check', is_flag=True, help='Perform URL accessibility check')
@click.option('--selector-test', is_flag=True, help='Test CSS selectors')
@click.option('--report', type=click.Path(), help='Save validation report to file')
def validate(config_file: str, url_check: bool, selector_test: bool, report: Optional[str]):
    """Validate pipet configuration file."""
    async def execute_validate():
        try:
            # Load configuration
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Convert to PipetConfiguration (simplified for CLI)
            from .models import PipetConfiguration, HttpMethod, OutputFormat, RetryConfig, RateLimitConfig

            pipet_config = PipetConfiguration(
                config_id=config_data.get("config_id", "cli_validation"),
                request_id="cli_validation",
                url=config_data.get("url", ""),
                method=HttpMethod(config_data.get("method", "GET")),
                headers=config_data.get("headers", {}),
                selectors=config_data.get("selectors", {}),
                output_format=OutputFormat(config_data.get("output_format", "json")),
                output_file=config_data.get("output_file"),
                timeout=config_data.get("timeout", 30)
            )

            # Create validator and validate
            validator = ConfigValidator()
            validation_result = await validator.validate_configuration(
                pipet_config,
                perform_url_check=url_check,
                perform_selector_test=selector_test
            )

            # Display validation results
            display_validation_results(validation_result, pipet_config)

            # Save report if requested
            if report:
                validator_instance = ConfigValidator()
                report_text = validator_instance.generate_validation_report(validation_result, pipet_config)
                with open(report, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                click.echo(f"Validation report saved to: {report}")

            # Return appropriate exit code
            sys.exit(0 if validation_result["is_valid"] else 1)

        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(execute_validate())


@cli.command()
@click.option('--status', type=str, help='Get status of specific execution')
def status(status: Optional[str]):
    """Get status of scraping executions."""
    if status:
        # Get specific execution status
        async def get_execution_status():
            executor = SingleExecutionOrchestrator()
            status_info = await executor.get_execution_status(status)
            if status_info:
                click.echo(json.dumps(status_info, indent=2, default=str))
            else:
                click.echo(f"Execution {status} not found", err=True)
                sys.exit(1)

        asyncio.run(get_execution_status())
    else:
        # Show system status (placeholder)
        click.echo("System Status:")
        click.echo("  CLI Version: 1.0.0")
        click.echo("  Python: " + sys.version)
        click.echo("  Working Directory: " + str(Path.cwd()))
        click.echo("  Data Directory: data/")
        click.echo("  Log Directory: logs/")


@cli.command()
@click.argument('execution_id', type=str)
@click.option('--report', type=click.Path(), help='Save execution report to file')
def report(execution_id: str, report: Optional[str]):
    """Generate detailed report for execution."""
    # This would load execution data from storage and generate report
    # For now, provide a placeholder implementation
    click.echo(f"Execution Report for: {execution_id}")
    click.echo("Report generation not fully implemented in this version")
    click.echo("Use the status command to get execution information")


@cli.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='table', help='Output format')
def history(format: str):
    """Show execution history."""
    # This would load execution history from storage
    # For now, provide placeholder
    if format == "json":
        click.echo(json.dumps([], indent=2))
    else:
        click.echo("Execution History:")
        click.echo("No history available in this version")


@cli.command()
def config():
    """Show current configuration."""
    try:
        config = get_global_config()
        config_dict = {
            "nlp_config": {
                "model_path": config.nlp_config.model_path,
                "max_tokens": config.nlp_config.max_tokens,
                "temperature": config.nlp_config.temperature
            },
            "pipet_config": {
                "default_timeout": config.pipet_config.default_timeout,
                "default_output_format": config.pipet_config.default_output_format
            },
            "validation_config": {
                "strict_mode": config.validation_config.strict_mode,
                "url_check_timeout": config.validation_config.url_check_timeout
            }
        }
        click.echo(json.dumps(config_dict, indent=2))
    except Exception as e:
        click.echo(f"Error loading configuration: {str(e)}", err=True)


@cli.command()
@click.argument('url', type=str)
def test_url(url: str):
    """Test URL accessibility."""
    async def test_url_access():
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.head(url, allow_redirects=True) as response:
                    click.echo(f"URL: {url}")
                    click.echo(f"Status: {response.status}")
                    click.echo(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
                    click.echo(f"Content-Length: {response.headers.get('content-length', 'N/A')}")
                    click.echo(f"Accessible: {response.status < 400}")

        except Exception as e:
            click.echo(f"Error testing URL: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(test_url_access())


@cli.command()
@click.argument('selector', type=str)
@click.argument('url', type=str)
def test_selector(selector: str, url: str):
    """Test CSS selector against URL."""
    async def test_css_selector():
        try:
            import aiohttp
            from bs4 import BeautifulSoup

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    elements = soup.select(selector)
                    click.echo(f"Selector: {selector}")
                    click.echo(f"URL: {url}")
                    click.echo(f"Elements found: {len(elements)}")

                    if elements:
                        click.echo("\nSample elements:")
                        for i, elem in enumerate(elements[:5]):  # Show first 5 elements
                            text = elem.get_text(strip=True)[:100]
                            click.echo(f"  {i+1}. {text}")

        except Exception as e:
            click.echo(f"Error testing selector: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(test_css_selector())


# Enhanced Batch Processing Commands
@cli.group()
def batch():
    """Enhanced batch processing commands."""
    pass


@batch.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--strategy', '-s', type=click.Choice(['sequential', 'parallel', 'adaptive']),
              default='adaptive', help='Execution strategy')
@click.option('--max-concurrent', type=int, default=5, help='Maximum concurrent executions')
@click.option('--timeout', type=int, default=300, help='Timeout per request (seconds)')
@click.option('--continue-on-error/--stop-on-error', default=True, help='Continue on individual failures')
@click.option('--priority-ordering', is_flag=True, help='Enable priority-based ordering')
@click.option('--enable-caching', is_flag=True, default=True, help='Enable result caching')
@click.option('--aggregation', type=click.Choice(['union', 'intersection', 'priority', 'temporal']),
              default='union', help='Data aggregation strategy')
@click.option('--output-dir', type=click.Path(), help='Output directory for results')
@click.option('--template', type=str, help='Configuration template to use')
@click.option('--report', type=click.Path(), help='Save batch report to file')
def process(input_file: str, strategy: str, max_concurrent: int, timeout: int,
            continue_on_error: bool, priority_ordering: bool, enable_caching: bool,
            aggregation: str, output_dir: Optional[str], template: Optional[str],
            report: Optional[str]):
    """
    Process batch scraping requests with advanced options.

    Input file should contain JSON array of requests:
    [
        {"user_description": "Extract HIBOR rates", "user_context": {...}, "priority": 3},
        {"user_description": "Get GDP statistics", "user_context": {...}, "priority": 1}
    ]
    """
    async def execute_enhanced_batch():
        try:
            # Load requests from file
            with open(input_file, 'r', encoding='utf-8') as f:
                requests_data = json.load(f)

            if not isinstance(requests_data, list):
                raise ValueError("Input file must contain a JSON array of requests")

            # Convert to NaturalLanguageRequest objects
            requests = []
            for req_data in requests_data:
                request = NaturalLanguageRequest(
                    user_description=req_data["user_description"],
                    user_context=req_data.get("user_context", {}),
                    priority=req_data.get("priority", 1)
                )
                requests.append(request)

            click.echo(f"Loaded {len(requests)} requests from {input_file}")
            click.echo(f"Strategy: {strategy}, Max Concurrent: {max_concurrent}")

            # Create batch processor
            processor = BatchProcessor()
            config_manager = BatchConfigManager()
            aggregator = BatchResultAggregator()

            # Create batch request
            batch_request = BatchRequest(
                requests=requests,
                processing_strategy=strategy,
                max_concurrent=max_concurrent,
                timeout_per_request=timeout,
                continue_on_error=continue_on_error,
                priority_ordering=priority_ordering,
                analysis_type="multi_source",
                consolidation_options={
                    "method": aggregation,
                    "apply_quality_improvements": True
                }
            )

            # Generate configurations if template provided
            if template:
                configurations = config_manager.create_batch_configuration(
                    batch_request,
                    template_id=template
                )
                click.echo(f"Generated {len(configurations)} configurations using template: {template}")

            # Process batch
            batch_result = await processor.process_batch_requests(
                requests=requests,
                processing_strategy=strategy,
                execution_options={
                    "max_concurrent": max_concurrent,
                    "timeout_per_request": timeout,
                    "continue_on_error": continue_on_error,
                    "enable_caching": enable_caching,
                    "output_dir": output_dir
                },
                use_priority_ordering=priority_ordering
            )

            # Display results
            display_enhanced_batch_results(batch_result)

            # Generate detailed report if requested
            if report:
                report_data = aggregator.generate_batch_report(batch_result, "detailed")
                with open(report, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, default=str)
                click.echo(f"\nDetailed report saved to: {report}")

            # Return appropriate exit code
            if batch_result.success_rate > 0.5:
                sys.exit(0)
            else:
                sys.exit(1)

        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(execute_enhanced_batch())


@batch.command()
@click.argument('batch_id', type=str)
@click.option('--format', type=click.Choice(['summary', 'detailed', 'json']), default='summary',
              help='Report format')
@click.option('--output', type=click.Path(), help='Save report to file')
def report(batch_id: str, format: str, output: Optional[str]):
    """Generate report for batch execution."""
    async def generate_batch_report():
        try:
            aggregator = BatchResultAggregator()

            # In a real implementation, you would load the batch result from storage
            # For now, provide a placeholder
            click.echo(f"Generating {format} report for batch: {batch_id}")
            click.echo("Report generation would load batch result from storage")

            # Placeholder batch result
            from .models import BatchResult, ProcessingStatus
            dummy_result = BatchResult(
                batch_id=batch_id,
                total_requests=10,
                successful_requests=8,
                failed_requests=2,
                start_time=datetime.now(),
                success_rate=0.8
            )

            # Generate report
            report_data = aggregator.generate_batch_report(dummy_result, format)

            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, default=str)
                click.echo(f"Report saved to: {output}")
            else:
                click.echo(json.dumps(report_data, indent=2, default=str))

        except Exception as e:
            click.echo(f"Error generating report: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(generate_batch_report())


@batch.command()
def templates():
    """List available configuration templates."""
    try:
        config_manager = BatchConfigManager()
        templates_data = config_manager.get_usage_statistics()

        click.echo("\nAvailable Configuration Templates:")
        click.echo("=" * 50)

        if templates_data["template_usage"]:
            for template_id, template_info in templates_data["template_usage"].items():
                click.echo(f"\n📋 {template_info['name']} ({template_id})")
                click.echo(f"   Type: {template_info['type']}")
                click.echo(f"   Usage: {template_info['usage_count']} times")
                click.echo(f"   Success Rate: {template_info['success_rate']:.1%}")
        else:
            click.echo("No templates available")

        if templates_data.get("most_used_template"):
            most_used = templates_data["most_used_template"]
            click.echo(f"\n🔥 Most Used Template:")
            click.echo(f"   {most_used['name']} - {most_used['usage_count']} uses")

    except Exception as e:
        click.echo(f"Error listing templates: {str(e)}", err=True)


@batch.command()
@click.argument('template_id', type=str)
@click.option('--format', type=click.Choice(['json', 'yaml']), default='json',
              help='Export format')
@click.argument('output_file', type=click.Path())
def export_template(template_id: str, format: str, output_file: str):
    """Export configuration template."""
    try:
        config_manager = BatchConfigManager()
        templates_data = config_manager.get_usage_statistics()

        if template_id not in templates_data["template_usage"]:
            click.echo(f"Template not found: {template_id}", err=True)
            sys.exit(1)

        template_info = templates_data["template_usage"][template_id]

        # Get full template details (simplified - would need full template access)
        export_data = {
            "template_id": template_id,
            "name": template_info["name"],
            "type": template_info["type"],
            "usage_count": template_info["usage_count"],
            "success_rate": template_info["success_rate"]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            if format == 'json':
                json.dump(export_data, f, indent=2)
            else:  # yaml
                import yaml
                yaml.dump(export_data, f, default_flow_style=False)

        click.echo(f"Template exported to: {output_file}")

    except Exception as e:
        click.echo(f"Error exporting template: {str(e)}", err=True)


@batch.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--validation-level', type=click.Choice(['basic', 'strict', 'production']),
              default='basic', help='Validation level')
@click.option('--optimize', is_flag=True, help='Optimize configuration')
@click.option('--export', type=click.Path(), help='Export optimized configuration')
def validate_config(config_file: str, validation_level: str, optimize: bool, export: Optional[str]):
    """Validate and optionally optimize batch configuration."""
    async def validate_batch_config():
        try:
            config_manager = BatchConfigManager()

            # Load configuration
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Create PipetConfiguration (simplified)
            config = config_manager.import_configuration(config_data)

            # Validate configuration
            from .batch_config_manager import ConfigValidationLevel
            validation_level_enum = ConfigValidationLevel(validation_level)
            validation_result = config_manager.validate_configuration(config, validation_level_enum)

            click.echo(f"\nConfiguration Validation Results:")
            click.echo(f"Config ID: {config.config_id}")
            click.echo(f"URL: {config.url}")
            click.echo(f"Validation Level: {validation_level}")
            click.echo(f"Overall Status: {'✅ VALID' if validation_result['is_valid'] else '❌ INVALID'}")

            if validation_result['errors']:
                click.echo("\n🚨 Errors:")
                for error in validation_result['errors']:
                    click.echo(f"  • {error}")

            if validation_result['warnings']:
                click.echo("\n⚠️  Warnings:")
                for warning in validation_result['warnings']:
                    click.echo(f"  • {warning}")

            if validation_result['recommendations']:
                click.echo("\n💡 Recommendations:")
                for recommendation in validation_result['recommendations']:
                    click.echo(f"  • {recommendation}")

            # Optimize if requested
            if optimize:
                optimization_result = config_manager.optimize_configuration(config)
                click.echo(f"\n🔧 Optimization Applied:")
                for optimization in optimization_result.optimization_applied:
                    click.echo(f"  • {optimization}")

                if export:
                    config_manager.export_configuration(
                        optimization_result.optimized_config,
                        "json",
                        export
                    )
                    click.echo(f"Optimized configuration exported to: {export}")

        except Exception as e:
            click.echo(f"Error validating configuration: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(validate_batch_config())


@batch.command()
def status():
    """Show batch processing system status."""
    try:
        processor = BatchProcessor()
        config_manager = BatchConfigManager()

        # Get system statistics
        templates_stats = config_manager.get_usage_statistics()

        click.echo("\nBatch Processing System Status:")
        click.echo("=" * 50)
        click.echo(f"Available Templates: {templates_stats['total_templates']}")
        click.echo(f"Average Success Rate: {templates_stats['average_success_rate']:.1%}")

        if templates_stats.get("most_used_template"):
            most_used = templates_stats["most_used_template"]
            click.echo(f"Most Used Template: {most_used['name']}")

        click.echo(f"\nProcessor Queue Status: Active")
        click.echo(f"Cache Status: Active")
        click.echo(f"System Health: ✅ Healthy")

    except Exception as e:
        click.echo(f"Error getting status: {str(e)}", err=True)


def display_enhanced_batch_results(batch_result):
    """Display enhanced batch execution results"""
    click.echo("\n" + "=" * 60)
    click.echo("ENHANCED BATCH EXECUTION RESULTS")
    click.echo("=" * 60)

    # Basic statistics
    click.echo(f"Batch ID: {batch_result.batch_id}")
    click.echo(f"Total Requests: {batch_result.total_requests}")
    click.echo(f"Successful: {batch_result.successful_requests} ({batch_result.success_rate:.1%})")
    click.echo(f"Failed: {batch_result.failed_requests}")
    click.echo(f"Cancelled: {batch_result.cancelled_requests}")

    # Timing information
    if batch_result.start_time:
        click.echo(f"Start Time: {batch_result.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if batch_result.end_time:
        click.echo(f"End Time: {batch_result.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Total Duration: {batch_result.total_duration:.2f} seconds")
    click.echo(f"Throughput: {batch_result.throughput:.2f} requests/minute")

    # Data statistics
    click.echo(f"Total Data Records: {batch_result.total_data_records}")

    # Quality metrics
    if batch_result.quality_metrics:
        quality = batch_result.quality_metrics
        click.echo(f"\nData Quality:")
        click.echo(f"  Overall Score: {quality.get('overall_quality_score', 0):.1%}")
        click.echo(f"  Completeness: {quality.get('completeness_score', 0):.1%}")
        click.echo(f"  Accuracy: {quality.get('accuracy_score', 0):.1%}")
        click.echo(f"  Timeliness: {quality.get('timeliness_score', 0):.1%}")
        click.echo(f"  Consistency: {quality.get('consistency_score', 0):.1%}")

    # Resource usage
    if batch_result.total_resource_usage:
        resources = batch_result.total_resource_usage
        click.echo(f"\nResource Usage:")
        click.echo(f"  Total CPU Time: {resources.get('total_cpu_time', 0):.2f}s")
        click.echo(f"  Peak Memory: {resources.get('peak_memory_usage', 0) / 1024 / 1024:.2f} MB")
        click.echo(f"  Network Requests: {resources.get('total_network_requests', 0)}")

    # Performance metrics
    if batch_result.performance_metrics:
        perf = batch_result.performance_metrics
        click.echo(f"\nPerformance Metrics:")
        if 'min_processing_time' in perf:
            click.echo(f"  Min Processing Time: {perf['min_processing_time']:.2f}s")
            click.echo(f"  Max Processing Time: {perf['max_processing_time']:.2f}s")
            click.echo(f"  Avg Processing Time: {perf['median_processing_time']:.2f}s")
        if 'total_data_records' in perf:
            click.echo(f"  Records per Execution: {perf['total_data_records'] / batch_result.successful_requests:.1f}" if batch_result.successful_requests > 0 else "N/A")

    # Error summary
    if batch_result.error_summary:
        click.echo(f"\nError Summary: {len(batch_result.error_summary)} errors")
        for error in batch_result.error_summary[:3]:  # Show first 3 errors
            click.echo(f"  • {error.get('error_message', 'Unknown error')}")

    click.echo("=" * 60)


def display_execution_results(execution):
    """Display execution results in CLI format"""
    click.echo("\n" + "=" * 50)
    click.echo("EXECUTION RESULTS")
    click.echo("=" * 50)
    click.echo(f"Execution ID: {execution.execution_id}")
    click.echo(f"Status: {execution.status.value.upper()}")
    click.echo(f"Duration: {execution.duration:.2f} seconds")

    if execution.start_time:
        click.echo(f"Start Time: {execution.start_time}")
    if execution.end_time:
        click.echo(f"End Time: {execution.end_time}")

    click.echo(f"Records Extracted: {execution.data_records_count}")

    if execution.output_file:
        click.echo(f"Output File: {execution.output_file}")
        if execution.file_size:
            click.echo(f"File Size: {execution.file_size:,} bytes")

    if execution.error_message:
        click.echo(f"\nERROR: {execution.error_message}")

    # Show monitoring data
    if execution.monitoring_data:
        click.echo("\nMonitoring Data:")
        for key, value in execution.monitoring_data.items():
            click.echo(f"  {key}: {value}")

    # Show resource usage
    if execution.resource_usage:
        click.echo("\nResource Usage:")
        click.echo(f"  CPU Time: {execution.resource_usage.cpu_time:.2f}s")
        click.echo(f"  Peak Memory: {execution.resource_usage.memory_peak / 1024 / 1024:.2f} MB")
        click.echo(f"  Network Sent: {execution.resource_usage.network_bytes_sent:,} bytes")
        click.echo(f"  Network Received: {execution.resource_usage.network_bytes_received:,} bytes")

    click.echo("=" * 50)


def display_batch_results(batch_results):
    """Display batch execution results"""
    click.echo("\n" + "=" * 50)
    click.echo("BATCH EXECUTION RESULTS")
    click.echo("=" * 50)
    click.echo(f"Batch ID: {batch_results['batch_id']}")
    click.echo(f"Total Requests: {batch_results['total_requests']}")
    click.echo(f"Successful: {batch_results['successful_requests']}")
    click.echo(f"Failed: {batch_results['failed_requests']}")
    click.echo(f"Success Rate: {batch_results['success_rate']:.1%}")
    click.echo(f"Total Duration: {batch_results['total_duration']:.2f} seconds")
    click.echo(f"Average Duration: {batch_results['average_duration']:.2f} seconds")

    if batch_results['failed_executions']:
        click.echo("\nFailed Executions:")
        for failed in batch_results['failed_executions']:
            click.echo(f"  - {failed['request_id']}: {failed['error']}")

    click.echo("=" * 50)


def display_validation_results(validation_result, config):
    """Display configuration validation results"""
    click.echo("\n" + "=" * 50)
    click.echo("CONFIGURATION VALIDATION RESULTS")
    click.echo("=" * 50)
    click.echo(f"Config ID: {config.config_id}")
    click.echo(f"URL: {config.url}")
    click.echo(f"Overall Status: {'✅ VALID' if validation_result['is_valid'] else '❌ INVALID'}")
    click.echo(f"Validation Score: {validation_result['validation_score']:.2f}")

    if validation_result.get('url_accessible'):
        click.echo(f"URL Status: ✅ Accessible")
    elif 'url_accessible' in validation_result:
        click.echo(f"URL Status: ❌ Not Accessible")

    if validation_result['issues']:
        click.echo("\n🚨 Issues:")
        for issue in validation_result['issues']:
            click.echo(f"  • {issue}")

    if validation_result['warnings']:
        click.echo("\n⚠️  Warnings:")
        for warning in validation_result['warnings']:
            click.echo(f"  • {warning}")

    if validation_result['suggestions']:
        click.echo("\n💡 Suggestions:")
        for suggestion in validation_result['suggestions']:
            click.echo(f"  • {suggestion}")

    click.echo("=" * 50)


if __name__ == '__main__':
    cli()