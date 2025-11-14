"""
Pipet configuration generator

Converts NLP processing results into executable pipet configurations
with proper selectors, extraction rules, and output formatting.
"""

import asyncio
import re
import yaml
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

from .models import (
    NLPProcessingResult, PipetConfiguration, HttpMethod, OutputFormat,
    RetryConfig, RateLimitConfig
)
from .exceptions import ConfigurationGenerationError
from .config import get_global_config
from .logging_config import StructuredLogger


class PipetConfigGenerator:
    """Generates pipet configurations from NLP processing results"""

    def __init__(self, config=None):
        self.logger = StructuredLogger("scraping.config_generator")
        self.config = config or get_global_config()
        self.pipet_config = self.config.pipet_config

        # Predefined selector patterns for common data types
        self.selector_patterns = self._load_selector_patterns()

    async def generate_configuration(self, nlp_result: NLPProcessingResult) -> PipetConfiguration:
        """
        Generate pipet configuration from NLP processing result

        Args:
            nlp_result: NLP processing result

        Returns:
            PipetConfiguration for execution

        Raises:
            ConfigurationGenerationError: If generation fails
        """
        try:
            self.logger.info(
                f"Generating pipet configuration",
                request_id=nlp_result.request_id,
                confidence_score=nlp_result.confidence_score,
                urls_count=len(nlp_result.extracted_urls),
                operation="generate_configuration"
            )

            # Validate input
            self._validate_nlp_result(nlp_result)

            # Select primary URL
            primary_url = self._select_primary_url(nlp_result.extracted_urls)

            # Determine HTTP method
            method = self._determine_http_method(primary_url, nlp_result.data_descriptions)

            # Generate CSS selectors
            selectors = await self._generate_css_selectors(
                primary_url,
                nlp_result.data_descriptions,
                nlp_result.output_requirements.get("fields", [])
            )

            # Generate extraction rules
            extraction_rules = await self._create_extraction_rules(
                nlp_result.output_requirements.get("fields", []),
                self._identify_data_type(nlp_result.data_descriptions)
            )

            # Create configuration
            config = PipetConfiguration(
                config_id=f"config_{nlp_result.request_id[:8]}",
                request_id=nlp_result.request_id,
                url=primary_url,
                method=method,
                headers=self._generate_request_headers(primary_url),
                selectors=selectors,
                extract_rules=extraction_rules,
                output_format=OutputFormat(nlp_result.output_requirements.get("format", "json")),
                output_file=self._generate_output_filename(
                    nlp_result.request_id,
                    nlp_result.output_requirements.get("format", "json")
                ),
                output_structure=self._create_output_structure(nlp_result.output_requirements),
                timeout=self._determine_timeout(primary_url, nlp_result.confidence_score),
                retry_config=self._generate_retry_config(
                    self._identify_source_type(primary_url),
                    self._assess_reliability(nlp_result)
                ),
                rate_limiting=self._generate_rate_limit_config(
                    self._identify_source_type(primary_url),
                    self._determine_politeness_level(nlp_result)
                ),
                confidence_score=nlp_result.confidence_score,
                model_version=nlp_result.model_version,
                validation_status="generated"
            )

            # Validate generated configuration
            self._validate_configuration(config)

            # Apply optimizations
            config = await self._apply_optimizations(config, nlp_result)

            self.logger.info(
                f"Configuration generated successfully",
                config_id=config.config_id,
                url=config.url,
                selector_count=len(config.selectors),
                operation="generate_configuration"
            )

            return config

        except ConfigurationGenerationError:
            raise
        except Exception as e:
            error_msg = f"Configuration generation failed: {str(e)}"
            self.logger.error(
                error_msg,
                request_id=nlp_result.request_id,
                operation="generate_configuration"
            )
            raise ConfigurationGenerationError(error_msg, nlp_result=nlp_result)

    def _validate_nlp_result(self, nlp_result: NLPProcessingResult) -> None:
        """Validate NLP result has sufficient information for configuration generation"""
        if not nlp_result.extracted_urls and not nlp_result.ambiguity_flags:
            raise ConfigurationGenerationError(
                "No URLs extracted and no ambiguities flagged",
                nlp_result=nlp_result
            )

        if nlp_result.confidence_score < 0.3:
            raise ConfigurationGenerationError(
                "Confidence score too low for reliable configuration generation",
                nlp_result=nlp_result
            )

    def _select_primary_url(self, urls: List[str]) -> str:
        """Select the most appropriate URL from extracted URLs"""
        if not urls:
            raise ConfigurationGenerationError("No URLs available for configuration")

        # Priority ranking for URL types
        url_priorities = {
            "hkma.gov.hk": 10,  # Hong Kong Monetary Authority
            "censtatd.gov.hk": 9,  # Census and Statistics Department
            "rvd.gov.hk": 8,  # Rating and Valuation Department
            "info.gov.hk": 7,  # Government Information
            "gov.hk": 6,  # Other government sites
        }

        # Score URLs based on domain priority and content
        scored_urls = []
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()

                # Base score from domain priority
                score = url_priorities.get(domain, 1)

                # Prefer HTTPS
                if parsed.scheme == "https":
                    score += 1

                # Prefer URLs with specific paths over root
                if parsed.path and parsed.path != "/":
                    score += 0.5

                scored_urls.append((score, url))

            except Exception:
                # Keep problematic URLs with lowest score
                scored_urls.append((0, url))

        # Return URL with highest score
        scored_urls.sort(key=lambda x: x[0], reverse=True)
        return scored_urls[0][1]

    def _determine_http_method(self, url: str, data_descriptions: List[str]) -> HttpMethod:
        """Determine appropriate HTTP method"""
        # Check for API endpoints
        if "/api/" in url or url.endswith("/api"):
            return HttpMethod.GET

        # Check for form submission indicators
        description_text = " ".join(data_descriptions).lower()
        if any(keyword in description_text for keyword in ["submit", "post", "search", "query"]):
            return HttpMethod.POST

        # Default to GET for data scraping
        return HttpMethod.GET

    async def _generate_css_selectors(
        self,
        url: str,
        data_descriptions: List[str],
        fields: List[str]
    ) -> Dict[str, str]:
        """Generate CSS selectors for data extraction"""
        selectors = {}

        try:
            # Identify data type for selector patterns
            data_type = self._identify_data_type(data_descriptions)

            # Get base selector patterns for this data type
            base_patterns = self.selector_patterns.get(data_type, self.selector_patterns["general"])

            # Generate field-specific selectors
            for field in fields:
                selector = self._generate_field_selector(field, data_type, base_patterns)
                selectors[field] = selector

            # Add backup selectors for robustness
            selectors.update(self._generate_backup_selectors(data_type, fields))

            return selectors

        except Exception as e:
            self.logger.warning(
                f"Failed to generate advanced selectors, using fallback: {str(e)}",
                url=url,
                data_type=data_type,
                operation="generate_css_selectors"
            )

            # Return generic selectors as fallback
            return self._generate_generic_selectors(fields)

    def _generate_field_selector(self, field: str, data_type: str, base_patterns: Dict[str, List[str]]) -> str:
        """Generate selector for a specific field"""
        field_mapping = {
            "date": base_patterns.get("date", ["table tr td:first-child", ".date", "[data-date]"]),
            "rate": base_patterns.get("rate", ["td:nth-child(2)", ".rate", ".value"]),
            "overnight_rate": base_patterns.get("overnight", ["td:nth-child(2)", ".overnight"]),
            "one_week_rate": base_patterns.get("week", ["td:nth-child(3)", ".week"]),
            "one_month_rate": base_patterns.get("month", ["td:nth-child(4)", ".month"]),
            "three_month_rate": base_patterns.get("three_month", ["td:nth-child(5)", ".quarter"]),
            "six_month_rate": base_patterns.get("six_month", ["td:nth-child(6)", ".half-year"]),
            "growth_rate": base_patterns.get("growth", ["td:last-child", ".growth", ".change"]),
            "amount": base_patterns.get("amount", ["td:nth-child(2)", ".amount", ".value"]),
            "index": base_patterns.get("index", ["td:nth-child(3)", ".index", ".value"])
        }

        # Get field-specific patterns
        patterns = field_mapping.get(field, base_patterns.get("general", ["td", ".value", "span"]))

        # Return the most specific pattern
        return patterns[0] if patterns else "td"

    def _generate_backup_selectors(self, data_type: str, fields: List[str]) -> Dict[str, str]:
        """Generate backup selectors for robustness"""
        backup_selectors = {}

        # Add numeric selectors as backup
        for i, field in enumerate(fields):
            backup_selectors[f"{field}_backup"] = f"td:nth-child({i + 1})"

        # Add common table patterns
        backup_selectors["table_data"] = "table.data-table tr"
        backup_selectors["generic_cell"] = "td"

        return backup_selectors

    def _generate_generic_selectors(self, fields: List[str]) -> Dict[str, str]:
        """Generate generic CSS selectors as fallback"""
        selectors = {}

        for i, field in enumerate(fields):
            selectors[field] = f"td:nth-child({i + 1})"

        # Add container selector
        selectors["container"] = "table tr"

        return selectors

    async def _create_extraction_rules(self, fields: List[str], data_type: str) -> Dict[str, Any]:
        """Create data extraction rules"""
        rules = {}

        # Basic table extraction
        rules["table"] = {
            "selector": "table",
            "multiple": True,
            "extract": {
                "rows": "tr:not(:first-child)",  # Skip header row
                "columns": ["td", "th"]
            }
        }

        # Field-specific extraction rules
        for field in fields:
            rules[field] = {
                "selector": f"td:nth-child({fields.index(field) + 1})",
                "type": self._determine_field_type(field),
                "required": self._is_field_required(field),
                "clean": self._get_cleaning_rules(field)
            }

        # Data transformation rules
        rules["transformations"] = self._create_transformation_rules(fields, data_type)

        return rules

    def _determine_field_type(self, field: str) -> str:
        """Determine the data type of a field"""
        type_mapping = {
            "date": "date",
            "time": "datetime",
            "rate": "number",
            "amount": "number",
            "index": "number",
            "growth": "number",
            "percentage": "number",
            "value": "text"
        }

        for key, field_type in type_mapping.items():
            if key in field.lower():
                return field_type

        return "text"

    def _is_field_required(self, field: str) -> bool:
        """Determine if a field is required"""
        required_fields = ["date", "value", "rate", "amount"]
        return any(req_field in field.lower() for req_field in required_fields)

    def _get_cleaning_rules(self, field: str) -> List[str]:
        """Get cleaning rules for a field"""
        cleaning_rules = ["strip_whitespace"]

        if "rate" in field.lower() or "percentage" in field.lower():
            cleaning_rules.extend(["remove_percent_sign", "convert_to_number"])

        if "amount" in field.lower():
            cleaning_rules.extend(["remove_currency", "convert_to_number"])

        if "date" in field.lower():
            cleaning_rules.append("standardize_date")

        return cleaning_rules

    def _create_transformation_rules(self, fields: List[str], data_type: str) -> Dict[str, Any]:
        """Create data transformation rules"""
        transformations = {
            "aggregation": {},
            "filtering": {},
            "sorting": {}
        }

        # Data type specific transformations
        if data_type == "interest_rates":
            transformations["filtering"] = {
                "remove_empty_rates": True,
                "min_rate": 0.0,
                "max_rate": 100.0
            }

        elif data_type == "gdp":
            transformations["filtering"] = {
                "positive_values_only": True,
                "min_value": 0
            }

        # Add field-specific transformations
        for field in fields:
            if "rate" in field.lower():
                transformations["aggregation"][field] = {
                    "calculate_average": True,
                    "calculate_trend": True
                }

        return transformations

    def _generate_request_headers(self, url: str) -> Dict[str, str]:
        """Generate appropriate HTTP headers"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-HK;q=0.8,zh;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        # Add specific headers for government websites
        if any(domain in url for domain in ["gov.hk", "gov.cn"]):
            headers["Accept-Language"] = "zh-HK,zh;q=0.9,en;q=0.8"

        # Add headers for API endpoints
        if "/api/" in url:
            headers["Content-Type"] = "application/json"
            headers["Accept"] = "application/json"

        return headers

    def _generate_output_filename(self, request_id: str, output_format: str) -> str:
        """Generate output filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_data_{request_id[:8]}_{timestamp}.{output_format}"
        return f"data/output/{filename}"

    def _create_output_structure(self, output_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create output structure definition"""
        fields = output_requirements.get("fields", [])

        structure = {
            "format": output_requirements.get("format", "json"),
            "fields": fields,
            "include_metadata": True,
            "sort_by": fields[0] if fields else None,
            "limit": None
        }

        return structure

    def _determine_timeout(self, url: str, confidence_score: float) -> int:
        """Determine appropriate timeout for the request"""
        base_timeout = 30

        # Adjust timeout based on source type
        if any(domain in url for domain in ["gov.hk", "gov.cn"]):
            base_timeout = 45  # Government sites can be slow

        # Adjust based on confidence
        if confidence_score < 0.7:
            base_timeout += 15  # More time for uncertain cases

        # Adjust based on URL complexity
        if "?" in url:  # Has query parameters
            base_timeout += 10

        return min(base_timeout, 120)  # Cap at 2 minutes

    def _generate_retry_config(self, source_type: str, reliability: str) -> RetryConfig:
        """Generate retry configuration"""
        base_retries = 3

        if source_type == "government":
            base_retries = 5  # More retries for government sites

        if reliability == "low":
            base_retries += 2

        return RetryConfig(
            max_retries=base_retries,
            retry_delay=2.0,
            backoff_factor=2.0,
            retry_on_status=[500, 502, 503, 504, 429, 408],
            max_retry_time=60.0
        )

    def _generate_rate_limit_config(self, source_type: str, politeness_level: str) -> RateLimitConfig:
        """Generate rate limiting configuration"""
        if source_type == "government":
            base_rate = 0.5  # Very conservative for government sites
        else:
            base_rate = 1.0

        if politeness_level == "high":
            base_rate *= 0.5
        elif politeness_level == "low":
            base_rate *= 1.5

        return RateLimitConfig(
            requests_per_second=max(0.1, min(base_rate, 5.0)),
            burst_limit=int(base_rate * 5),
            cooldown_period=10.0 if politeness_level == "high" else 5.0
        )

    def _identify_data_type(self, data_descriptions: List[str]) -> str:
        """Identify data type from descriptions"""
        text = " ".join(data_descriptions).lower()

        type_mapping = {
            "interest_rates": ["hibor", "利率", "interest", "rate"],
            "gdp": ["gdp", "國內生產總值", "economic"],
            "unemployment": ["失業", "unemployment", "就業"],
            "property_prices": ["樓價", "物業", "property", "housing"],
            "trade": ["貿易", "trade", "進出口"],
            "inflation": ["cpi", "消費物價", "inflation"]
        }

        for data_type, keywords in type_mapping.items():
            if any(keyword in text for keyword in keywords):
                return data_type

        return "general"

    def _identify_source_type(self, url: str) -> str:
        """Identify source type from URL"""
        if any(domain in url for domain in ["gov.hk", "gov.cn", "gov.tw"]):
            return "government"
        elif any(domain in url for domain in ["edu.hk", "edu.cn"]):
            return "education"
        elif any(domain in url for domain in ["com"]):
            return "commercial"
        else:
            return "general"

    def _assess_reliability(self, nlp_result: NLPProcessingResult) -> str:
        """Assess reliability of the NLP result"""
        if nlp_result.confidence_score > 0.8:
            return "high"
        elif nlp_result.confidence_score > 0.5:
            return "medium"
        else:
            return "low"

    def _determine_politeness_level(self, nlp_result: NLPProcessingResult) -> str:
        """Determine politeness level for rate limiting"""
        if nlp_result.confidence_score < 0.6 or nlp_result.ambiguity_flags:
            return "high"  # Be more polite when uncertain
        elif nlp_result.confidence_score > 0.9:
            return "medium"
        else:
            return "medium"

    def _validate_configuration(self, config: PipetConfiguration) -> None:
        """Validate generated configuration"""
        if not config.url:
            raise ConfigurationGenerationError("Generated configuration has no URL")

        if not config.selectors:
            raise ConfigurationGenerationError("Generated configuration has no selectors")

        if not config.output_format:
            raise ConfigurationGenerationError("Generated configuration has no output format")

    async def _apply_optimizations(self, config: PipetConfiguration, nlp_result: NLPProcessingResult) -> PipetConfiguration:
        """Apply optimizations to the configuration"""
        # Performance optimizations
        config = await self._optimize_for_performance(config)

        # Reliability optimizations
        config = await self._optimize_for_reliability(config)

        # Add security headers
        config = self._add_security_headers(config)

        # Add optimization history
        config.optimization_history.extend([
            "performance_optimization",
            "reliability_optimization",
            "security_hardening"
        ])

        return config

    async def _optimize_for_performance(self, config: PipetConfiguration) -> PipetConfiguration:
        """Apply performance optimizations"""
        # Optimize timeout
        if config.timeout > 60:
            config.timeout = max(30, config.timeout - 15)

        # Optimize selectors for efficiency
        for field, selector in config.selectors.items():
            # Avoid overly complex selectors
            if len(selector) > 100:
                config.selectors[field] = "td"

        return config

    async def _optimize_for_reliability(self, config: PipetConfiguration) -> PipetConfiguration:
        """Apply reliability optimizations"""
        # Increase retry count for important sources
        if self._identify_source_type(config.url) == "government":
            config.retry_config.max_retries = max(5, config.retry_config.max_retries)

        # Add conservative rate limiting for government sites
        if self._identify_source_type(config.url) == "government":
            config.rate_limiting.requests_per_second = min(
                config.rate_limiting.requests_per_second, 0.5
            )

        return config

    def _add_security_headers(self, config: PipetConfiguration) -> PipetConfiguration:
        """Add security-related headers"""
        security_headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }

        config.headers.update(security_headers)
        return config

    def _load_selector_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Load predefined CSS selector patterns"""
        return {
            "interest_rates": {
                "date": ["table tr td:first-child", ".date", ".time"],
                "rate": ["table tr td:not(:first-child)", ".rate", ".value"],
                "overnight": ["td:nth-child(2)", ".overnight", ".o_n"],
                "week": ["td:nth-child(3)", ".week", ".1w"],
                "month": ["td:nth-child(4)", ".month", ".1m"],
                "three_month": ["td:nth-child(5)", ".quarter", ".3m"],
                "six_month": ["td:nth-child(6)", ".half-year", ".6m"]
            },
            "gdp": {
                "quarter": ["tr td:first-child", ".period", ".time"],
                "amount": ["tr td:nth-child(2)", ".amount", ".value"],
                "growth": ["tr td:last-child", ".growth", ".change"]
            },
            "unemployment": {
                "month": ["tr td:first-child", ".date", ".period"],
                "rate": ["tr td:nth-child(2)", ".unemployment", ".rate"],
                "underemployment": ["tr td:nth-child(3)", ".underemployment"]
            },
            "property_prices": {
                "month": ["tr td:first-child", ".date", ".period"],
                "property_type": ["tr td:nth-child(2)", ".type", ".category"],
                "index": ["tr td:last-child", ".index", ".price"]
            },
            "general": {
                "date": ["td:first-child", ".date", "[data-date]"],
                "value": ["td:not(:first-child)", ".value", ".data"],
                "amount": ["td:nth-child(2)", ".amount", ".number"],
                "index": ["td:last-child", ".index", ".value"]
            }
        }

    def generate_yaml_config(self, config: PipetConfiguration) -> str:
        """Generate YAML configuration for pipet"""
        yaml_data = {
            "url": config.url,
            "method": config.method.value.lower(),
            "headers": config.headers,
            "extract": {
                **config.selectors,
                **config.extract_rules
            },
            "output": {
                "format": config.output_format.value,
                "file": config.output_file
            },
            "retry": {
                "max_retries": config.retry_config.max_retries,
                "delay": config.retry_config.retry_delay,
                "backoff": config.retry_config.backoff_factor,
                "max_time": config.retry_config.max_retry_time
            },
            "timeout": config.timeout
        }

        # Add payload if present
        if config.payload:
            yaml_data["payload"] = config.payload

        return yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True)

    async def batch_generate_configurations(self, nlp_results: List[NLPProcessingResult]) -> List[PipetConfiguration]:
        """Generate configurations for multiple NLP results"""
        configs = []

        # Generate configurations concurrently
        tasks = [self.generate_configuration(result) for result in nlp_results]

        try:
            configs = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions in results
            processed_configs = []
            for i, result in enumerate(configs):
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Configuration generation failed for result {i}: {str(result)}",
                        operation="batch_generate_configurations"
                    )
                    # Create minimal config for failed cases
                    minimal_config = PipetConfiguration(
                        config_id=f"error_config_{i}",
                        request_id=nlp_results[i].request_id,
                        url="https://example.com",
                        method=HttpMethod.GET,
                        selectors={},
                        output_format=OutputFormat.JSON,
                        confidence_score=0.0,
                        model_version="error"
                    )
                    processed_configs.append(minimal_config)
                else:
                    processed_configs.append(result)

            return processed_configs

        except Exception as e:
            self.logger.error(
                f"Batch configuration generation failed: {str(e)}",
                batch_size=len(nlp_results),
                operation="batch_generate_configurations"
            )
            raise ConfigurationGenerationError(f"Batch generation failed: {str(e)}")


# Convenience functions
def create_config_generator(config=None) -> PipetConfigGenerator:
    """Create configuration generator instance"""
    return PipetConfigGenerator(config)