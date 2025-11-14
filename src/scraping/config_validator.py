"""
Configuration validator for pipet configurations

Provides comprehensive validation and verification of generated pipet configurations
including selector testing, URL accessibility, and configuration completeness.
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

from .models import PipetConfiguration, HttpMethod, OutputFormat
from .exceptions import ValidationError
from .logging_config import StructuredLogger


class ConfigValidator:
    """Validator for pipet configurations"""

    def __init__(self):
        self.logger = StructuredLogger("scraping.config_validator")
        self.session_timeout = aiohttp.ClientTimeout(total=10)

    async def validate_configuration(
        self,
        config: PipetConfiguration,
        perform_url_check: bool = True,
        perform_selector_test: bool = False
    ) -> Dict[str, Any]:
        """
        Validate pipet configuration comprehensively

        Args:
            config: Pipet configuration to validate
            perform_url_check: Whether to check URL accessibility
            perform_selector_test: Whether to test CSS selectors

        Returns:
            Validation result with status and issues
        """
        validation_result = {
            "is_valid": True,
            "validation_score": 1.0,
            "issues": [],
            "warnings": [],
            "suggestions": [],
            "url_accessible": False,
            "selector_results": {},
            "validation_timestamp": datetime.now().isoformat()
        }

        try:
            self.logger.info(
                f"Starting configuration validation",
                config_id=config.config_id,
                url=config.url,
                perform_url_check=perform_url_check,
                operation="validate_configuration"
            )

            # Basic structure validation
            self._validate_basic_structure(config, validation_result)

            # URL validation and accessibility check
            await self._validate_url(config.url, validation_result, perform_url_check)

            # Selector validation
            await self._validate_selectors(config.selectors, validation_result, perform_selector_test)

            # Output configuration validation
            self._validate_output_config(config, validation_result)

            # Execution configuration validation
            self._validate_execution_config(config, validation_result)

            # Security validation
            self._validate_security(config, validation_result)

            # Calculate overall validation score
            self._calculate_validation_score(validation_result)

            # Determine final validation status
            validation_result["is_valid"] = (
                validation_result["validation_score"] >= 0.7 and
                len([i for i in validation_result["issues"] if i.startswith("CRITICAL")]) == 0
            )

            self.logger.info(
                f"Configuration validation completed",
                config_id=config.config_id,
                is_valid=validation_result["is_valid"],
                validation_score=validation_result["validation_score"],
                issues_count=len(validation_result["issues"]),
                warnings_count=len(validation_result["warnings"]),
                operation="validate_configuration"
            )

            return validation_result

        except Exception as e:
            self.logger.error(
                f"Configuration validation failed: {str(e)}",
                config_id=config.config_id,
                operation="validate_configuration"
            )
            raise ValidationError(f"Validation failed: {str(e)}", validation_issues=[str(e)])

    def _validate_basic_structure(self, config: PipetConfiguration, result: Dict[str, Any]) -> None:
        """Validate basic configuration structure"""
        # Required fields check
        required_fields = ["config_id", "request_id", "url", "method", "output_format"]
        for field in required_fields:
            if not hasattr(config, field) or getattr(config, field) is None:
                result["issues"].append(f"CRITICAL: Missing required field '{field}'")

        # URL format validation
        try:
            parsed = urlparse(config.url)
            if not parsed.scheme or not parsed.netloc:
                result["issues"].append("CRITICAL: Invalid URL format")
        except Exception:
            result["issues"].append("CRITICAL: URL parsing error")

        # Method validation
        if config.method not in [HttpMethod.GET, HttpMethod.POST]:
            result["warnings"].append(f"Unusual HTTP method: {config.method}")

        # Output format validation
        valid_formats = [OutputFormat.JSON, OutputFormat.CSV, OutputFormat.XML, OutputFormat.YAML]
        if config.output_format not in valid_formats:
            result["issues"].append(f"Invalid output format: {config.output_format}")

    async def _validate_url(
        self,
        url: str,
        result: Dict[str, Any],
        perform_check: bool
    ) -> None:
        """Validate URL and check accessibility if requested"""
        if not url:
            result["issues"].append("CRITICAL: No URL specified")
            return

        # Basic URL validation
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                result["issues"].append(f"Unsupported URL scheme: {parsed.scheme}")

            # Check for localhost URLs
            if parsed.netloc in ["localhost", "127.0.0.1"]:
                result["warnings"].append("Localhost URL may not work in production")

        except Exception as e:
            result["issues"].append(f"URL validation error: {str(e)}")
            return

        # Accessibility check
        if perform_check:
            await self._check_url_accessibility(url, result)

    async def _check_url_accessibility(self, url: str, result: Dict[str, Any]) -> None:
        """Check if URL is accessible"""
        try:
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.head(url, allow_redirects=True) as response:
                    result["url_accessible"] = True
                    result["url_status_code"] = response.status
                    result["url_content_type"] = response.headers.get("content-type", "")

                    if response.status >= 400:
                        result["warnings"].append(f"URL returns error status: {response.status}")
                    elif response.status >= 300:
                        result["suggestions"].append(f"URL redirects (status: {response.status})")

        except asyncio.TimeoutError:
            result["warnings"].append("URL accessibility check timed out")
            result["url_accessible"] = False
        except Exception as e:
            result["warnings"].append(f"URL accessibility check failed: {str(e)}")
            result["url_accessible"] = False

    async def _validate_selectors(
        self,
        selectors: Dict[str, str],
        result: Dict[str, Any],
        perform_test: bool
    ) -> None:
        """Validate CSS selectors"""
        if not selectors:
            result["issues"].append("CRITICAL: No CSS selectors specified")
            return

        # Basic selector syntax validation
        for field_name, selector in selectors.items():
            if not selector or not selector.strip():
                result["issues"].append(f"Empty selector for field '{field_name}'")
                continue

            # Check for obvious syntax errors
            if self._has_selector_syntax_errors(selector):
                result["warnings"].append(f"Potential syntax error in selector '{field_name}': {selector}")

            # Check for overly complex selectors
            if len(selector) > 200:
                result["suggestions"].append(f"Very complex selector for '{field_name}', consider simplification")

        # Optional selector testing (would require actual page content)
        if perform_test:
            await self._test_selectors(selectors, result)

    def _has_selector_syntax_errors(self, selector: str) -> bool:
        """Check for obvious CSS selector syntax errors"""
        syntax_errors = [
            r'\[\s*$',  # Unclosed attribute selector
            r'\(\s*$',  # Unclosed parenthesis
            r'^\s*[>+~]\s*$',  # Selector starts with combinator without element
            r'[>+~]{2,}',  # Multiple consecutive combinators
            r'\]\s*\[',  # Missing content between attribute selectors
        ]

        for pattern in syntax_errors:
            if re.search(pattern, selector):
                return True

        return False

    async def _test_selectors(self, selectors: Dict[str, str], result: Dict[str, Any]) -> None:
        """Test CSS selectors against actual content"""
        # This would require fetching the actual page content and testing selectors
        # For now, we'll simulate basic testing

        selector_results = {}

        for field_name, selector in selectors.items():
            try:
                # Simulate selector testing
                # In real implementation, this would use BeautifulSoup or similar
                test_result = {
                    "selector": selector,
                    "testable": True,
                    "estimated_specificity": self._calculate_selector_specificity(selector),
                    "common_pattern": self._identify_common_pattern(selector)
                }

                selector_results[field_name] = test_result

            except Exception as e:
                selector_results[field_name] = {
                    "selector": selector,
                    "testable": False,
                    "error": str(e)
                }
                result["warnings"].append(f"Selector test failed for '{field_name}': {str(e)}")

        result["selector_results"] = selector_results

    def _calculate_selector_specificity(self, selector: str) -> int:
        """Calculate CSS selector specificity score"""
        # Simplified specificity calculation
        id_count = len(re.findall(r'#', selector))
        class_count = len(re.findall(r'\.', selector))
        attr_count = len(re.findall(r'\[', selector))

        # Calculate specificity (IDs are most specific)
        return id_count * 100 + class_count * 10 + attr_count

    def _identify_common_pattern(self, selector: str) -> str:
        """Identify common CSS selector patterns"""
        patterns = {
            "table_based": r"table|tr|td|th",
            "class_based": r"\.\w+",
            "id_based": r"#\w+",
            "attribute_based": r"\[\w+\]",
            "nth_child": r":nth-child",
            "pseudo_class": r":[\w-]+"
        }

        for pattern_name, pattern in patterns.items():
            if re.search(pattern, selector):
                return pattern_name

        return "generic"

    def _validate_output_config(self, config: PipetConfiguration, result: Dict[str, Any]) -> None:
        """Validate output configuration"""
        # Output format validation
        if not config.output_format:
            result["issues"].append("CRITICAL: No output format specified")
            return

        # Output file validation
        if config.output_file:
            try:
                output_path = Path(config.output_file)
                output_dir = output_path.parent

                # Check if directory exists or can be created
                if not output_dir.exists():
                    result["warnings"].append(f"Output directory does not exist: {output_dir}")
                    result["suggestions"].append(f"Create directory: {output_dir}")

                # Check file extension matches format
                format_extensions = {
                    OutputFormat.JSON: ".json",
                    OutputFormat.CSV: ".csv",
                    OutputFormat.XML: ".xml",
                    OutputFormat.YAML: ".yaml"
                }

                expected_ext = format_extensions.get(config.output_format)
                if expected_ext and not config.output_file.endswith(expected_ext):
                    result["warnings"].append(
                        f"File extension doesn't match format. Expected: {expected_ext}, Got: {output_path.suffix}"
                    )

            except Exception as e:
                result["issues"].append(f"Output file validation error: {str(e)}")

    def _validate_execution_config(self, config: PipetConfiguration, result: Dict[str, Any]) -> None:
        """Validate execution configuration"""
        # Timeout validation
        if config.timeout <= 0:
            result["issues"].append("Timeout must be greater than 0")
        elif config.timeout > 300:  # 5 minutes
            result["warnings"].append("Very long timeout may indicate inefficient scraping")

        # Retry configuration validation
        if config.retry_config:
            if config.retry_config.max_retries > 10:
                result["warnings"].append("High retry count may cause performance issues")

            if config.retry_config.retry_delay < 0.1:
                result["issues"].append("Retry delay must be at least 0.1 seconds")
            elif config.retry_config.retry_delay > 60:
                result["warnings"].append("Long retry delay may cause poor user experience")

            if config.retry_config.backoff_factor < 1.0:
                result["issues"].append("Backoff factor must be at least 1.0")

        # Rate limiting validation
        if config.rate_limiting:
            if config.rate_limiting.requests_per_second > 10:
                result["warnings"].append("High request rate may be blocked by target servers")

            if config.rate_limiting.requests_per_second < 0.1:
                result["suggestions"].append("Very low request rate may be too conservative")

    def _validate_security(self, config: PipetConfiguration, result: Dict[str, Any]) -> None:
        """Validate security aspects"""
        # Check for sensitive URLs
        parsed = urlparse(config.url)
        if parsed.netloc in ["localhost", "127.0.0.1", "0.0.0.0"]:
            result["warnings"].append("Local URL detected, ensure this is intentional")

        # Check headers for security
        if config.headers:
            # Check for authentication headers
            auth_headers = ["authorization", "cookie", "session"]
            for header in auth_headers:
                if header.lower() in [h.lower() for h in config.headers.keys()]:
                    result["warnings"].append(f"Authentication header '{header}' detected, ensure secure handling")

            # Recommend security headers
            recommended_headers = ["User-Agent", "Accept", "Accept-Language"]
            missing_headers = [h for h in recommended_headers if h not in config.headers]
            if missing_headers:
                result["suggestions"].append(f"Consider adding headers: {', '.join(missing_headers)}")

    def _calculate_validation_score(self, result: Dict[str, Any]) -> None:
        """Calculate overall validation score"""
        score = 1.0

        # Deduct points for issues
        critical_issues = [i for i in result["issues"] if i.startswith("CRITICAL")]
        score -= len(critical_issues) * 0.3

        other_issues = [i for i in result["issues"] if not i.startswith("CRITICAL")]
        score -= len(other_issues) * 0.2

        # Deduct points for warnings
        score -= len(result["warnings"]) * 0.05

        # Add points for successful checks
        if result.get("url_accessible"):
            score += 0.1

        if result.get("selector_results"):
            score += 0.05

        # Ensure score is within valid range
        result["validation_score"] = max(0.0, min(1.0, score))

    async def validate_multiple_configurations(
        self,
        configs: List[PipetConfiguration],
        perform_url_check: bool = False,  # Disabled by default for batch validation
        perform_selector_test: bool = False
    ) -> Dict[str, Any]:
        """
        Validate multiple configurations

        Args:
            configs: List of configurations to validate
            perform_url_check: Whether to check URL accessibility
            perform_selector_test: Whether to test CSS selectors

        Returns:
            Batch validation results
        """
        validation_results = {}

        # Validate configurations concurrently
        tasks = [
            self.validate_configuration(
                config, perform_url_check, perform_selector_test
            )
            for config in configs
        ]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, (config, result) in enumerate(zip(configs, results)):
                if isinstance(result, Exception):
                    validation_results[config.config_id] = {
                        "is_valid": False,
                        "validation_score": 0.0,
                        "issues": [f"Validation failed: {str(result)}"],
                        "warnings": [],
                        "suggestions": [],
                        "validation_timestamp": datetime.now().isoformat()
                    }
                else:
                    validation_results[config.config_id] = result

            # Calculate batch statistics
            valid_count = sum(1 for r in validation_results.values() if r["is_valid"])
            total_count = len(validation_results)
            avg_score = sum(r["validation_score"] for r in validation_results.values()) / total_count

            batch_summary = {
                "total_configurations": total_count,
                "valid_configurations": valid_count,
                "invalid_configurations": total_count - valid_count,
                "validation_rate": valid_count / total_count,
                "average_score": avg_score,
                "validation_timestamp": datetime.now().isoformat()
            }

            return {
                "batch_summary": batch_summary,
                "individual_results": validation_results
            }

        except Exception as e:
            self.logger.error(
                f"Batch validation failed: {str(e)}",
                batch_size=len(configs),
                operation="validate_multiple_configurations"
            )
            raise ValidationError(f"Batch validation failed: {str(e)}")

    def generate_validation_report(
        self,
        validation_result: Dict[str, Any],
        config: PipetConfiguration
    ) -> str:
        """Generate human-readable validation report"""
        report = []
        report.append(f"Configuration Validation Report")
        report.append(f"=" * 40)
        report.append(f"Config ID: {config.config_id}")
        report.append(f"URL: {config.url}")
        report.append(f"Validation Timestamp: {validation_result['validation_timestamp']}")
        report.append("")

        # Overall status
        status = "✅ VALID" if validation_result["is_valid"] else "❌ INVALID"
        score = validation_result["validation_score"]
        report.append(f"Overall Status: {status} (Score: {score:.2f})")
        report.append("")

        # URL status
        if "url_accessible" in validation_result:
            url_status = "✅ Accessible" if validation_result["url_accessible"] else "❌ Not Accessible"
            report.append(f"URL Status: {url_status}")
            if "url_status_code" in validation_result:
                report.append(f"HTTP Status: {validation_result['url_status_code']}")
            report.append("")

        # Issues
        if validation_result["issues"]:
            report.append("🚨 Issues:")
            for issue in validation_result["issues"]:
                report.append(f"  • {issue}")
            report.append("")

        # Warnings
        if validation_result["warnings"]:
            report.append("⚠️  Warnings:")
            for warning in validation_result["warnings"]:
                report.append(f"  • {warning}")
            report.append("")

        # Suggestions
        if validation_result["suggestions"]:
            report.append("💡 Suggestions:")
            for suggestion in validation_result["suggestions"]:
                report.append(f"  • {suggestion}")
            report.append("")

        # Selector results
        if validation_result.get("selector_results"):
            report.append("🔍 Selector Analysis:")
            for field, selector_result in validation_result["selector_results"].items():
                if selector_result.get("testable"):
                    specificity = selector_result.get("estimated_specificity", 0)
                    pattern = selector_result.get("common_pattern", "unknown")
                    report.append(f"  • {field}: Specificity {specificity}, Pattern: {pattern}")
                else:
                    report.append(f"  • {field}: Not testable")
            report.append("")

        return "\n".join(report)


# Convenience functions
def create_config_validator() -> ConfigValidator:
    """Create config validator instance"""
    return ConfigValidator()


async def validate_configuration(
    config: PipetConfiguration,
    perform_url_check: bool = True,
    perform_selector_test: bool = False
) -> Dict[str, Any]:
    """Validate a single configuration"""
    validator = ConfigValidator()
    return await validator.validate_configuration(config, perform_url_check, perform_selector_test)


async def validate_configurations(
    configs: List[PipetConfiguration],
    perform_url_check: bool = False,
    perform_selector_test: bool = False
) -> Dict[str, Any]:
    """Validate multiple configurations"""
    validator = ConfigValidator()
    return await validator.validate_multiple_configurations(
        configs, perform_url_check, perform_selector_test
    )