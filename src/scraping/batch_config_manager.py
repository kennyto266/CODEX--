"""
Batch configuration manager for managing batch scraping configurations

Handles configuration templates, validation, optimization, and persistence
for batch processing operations.
"""

import json
import os
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from .models import (
    BatchRequest, PipetConfiguration, NaturalLanguageRequest,
    ProcessingStatus, HttpMethod, OutputFormat, RateLimitConfig, RetryConfig
)
from .exceptions import ValidationError, ConfigurationError
from .logging_config import StructuredLogger
from .config import get_global_config


class ConfigTemplateType(str, Enum):
    """Configuration template types"""
    ECONOMIC_DATA = "economic_data"
    MARKET_DATA = "market_data"
    GOVERNMENT_STATS = "government_stats"
    FINANCIAL_REPORTS = "financial_reports"
    NEWS_SCRAPE = "news_scrape"
    CUSTOM = "custom"


class ConfigValidationLevel(str, Enum):
    """Configuration validation levels"""
    BASIC = "basic"  # Basic field validation
    STRICT = "strict"  # Comprehensive validation
    PRODUCTION = "production"  # Production-ready validation


@dataclass
class ConfigTemplate:
    """Configuration template for common scraping scenarios"""

    template_id: str
    template_type: ConfigTemplateType
    name: str
    description: str
    default_config: Dict[str, Any]
    required_fields: List[str]
    optional_fields: List[str]
    validation_rules: Dict[str, Any]
    optimization_suggestions: List[str]
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    success_rate: float = 0.0


@dataclass
class ConfigOptimization:
    """Configuration optimization result"""

    config_id: str
    original_config: PipetConfiguration
    optimized_config: PipetConfiguration
    optimization_applied: List[str]
    performance_improvement: Dict[str, float]
    validation_results: Dict[str, Any]
    optimization_timestamp: datetime


class BatchConfigManager:
    """Manager for batch scraping configurations"""

    def __init__(self, config_dir: Optional[str] = None):
        self.logger = StructuredLogger.get_logger(__name__)
        self.global_config = get_global_config()

        # Configuration directory
        self.config_dir = Path(config_dir or self.global_config.get("config_dir", "configs/scraping"))
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Template storage
        self.templates: Dict[str, ConfigTemplate] = {}
        self.template_file = self.config_dir / "templates.json"

        # Configuration cache
        self.config_cache: Dict[str, PipetConfiguration] = {}
        self.optimization_cache: Dict[str, ConfigOptimization] = {}

        # Load existing templates
        self._load_templates()

        # Initialize default templates
        self._initialize_default_templates()

    def _load_templates(self) -> None:
        """Load existing configuration templates"""
        try:
            if self.template_file.exists():
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    templates_data = json.load(f)

                for template_id, template_data in templates_data.items():
                    # Convert datetime strings back to datetime objects
                    template_data['created_at'] = datetime.fromisoformat(template_data['created_at'])
                    template_data['updated_at'] = datetime.fromisoformat(template_data['updated_at'])

                    template = ConfigTemplate(**template_data)
                    self.templates[template_id] = template

                self.logger.info(
                    "Loaded configuration templates",
                    template_count=len(self.templates)
                )
            else:
                self.logger.info("No existing template file found, will create new one")

        except Exception as e:
            self.logger.error(
                "Failed to load configuration templates",
                error=str(e),
                template_file=str(self.template_file)
            )

    def _save_templates(self) -> None:
        """Save configuration templates to file"""
        try:
            templates_data = {}
            for template_id, template in self.templates.items():
                # Convert datetime objects to ISO strings for JSON serialization
                template_dict = asdict(template)
                template_dict['created_at'] = template.created_at.isoformat()
                template_dict['updated_at'] = template.updated_at.isoformat()
                template_dict['template_type'] = template.template_type.value

                templates_data[template_id] = template_dict

            with open(self.template_file, 'w', encoding='utf-8') as f:
                json.dump(templates_data, f, indent=2, ensure_ascii=False)

            self.logger.info(
                "Saved configuration templates",
                template_count=len(self.templates)
            )

        except Exception as e:
            self.logger.error(
                "Failed to save configuration templates",
                error=str(e),
                template_file=str(self.template_file)
            )

    def _initialize_default_templates(self) -> None:
        """Initialize default configuration templates"""

        # Economic data template
        economic_template = ConfigTemplate(
            template_id="economic_data_default",
            template_type=ConfigTemplateType.ECONOMIC_DATA,
            name="Economic Data Scraper",
            description="Template for scraping economic data from government websites",
            default_config={
                "method": HttpMethod.GET,
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                },
                "timeout": 30,
                "output_format": OutputFormat.JSON,
                "retry_config": {
                    "max_retries": 3,
                    "retry_delay": 2.0,
                    "backoff_factor": 2.0
                },
                "rate_limiting": {
                    "requests_per_second": 1.0,
                    "burst_limit": 5,
                    "cooldown_period": 10.0
                }
            },
            required_fields=["url", "selectors"],
            optional_fields=["headers", "payload", "data_transformations"],
            validation_rules={
                "url": {"pattern": r"https?://.*", "required": True},
                "timeout": {"min": 1, "max": 300, "required": True}
            },
            optimization_suggestions=[
                "Use cache for economic data that updates infrequently",
                "Implement rate limiting for government websites",
                "Schedule scraping during off-peak hours"
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Market data template
        market_template = ConfigTemplate(
            template_id="market_data_default",
            template_type=ConfigTemplateType.MARKET_DATA,
            name="Market Data Scraper",
            description="Template for scraping financial market data",
            default_config={
                "method": HttpMethod.GET,
                "headers": {
                    "User-Agent": "Mozilla/5.0 (compatible; MarketDataBot/1.0)",
                    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9"
                },
                "timeout": 15,
                "output_format": OutputFormat.JSON,
                "retry_config": {
                    "max_retries": 5,
                    "retry_delay": 1.0,
                    "backoff_factor": 1.5
                },
                "rate_limiting": {
                    "requests_per_second": 2.0,
                    "burst_limit": 10,
                    "cooldown_period": 5.0
                }
            },
            required_fields=["url", "selectors"],
            optional_fields=["headers", "payload"],
            validation_rules={
                "url": {"pattern": r"https?://.*", "required": True},
                "timeout": {"min": 5, "max": 60, "required": True}
            },
            optimization_suggestions=[
                "Use WebSocket for real-time market data if available",
                "Implement caching for recent market data",
                "Consider API alternatives for market data"
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Add templates if they don't exist
        if economic_template.template_id not in self.templates:
            self.templates[economic_template.template_id] = economic_template

        if market_template.template_id not in self.templates:
            self.templates[market_template.template_id] = market_template

        # Save templates
        self._save_templates()

    def create_configuration_from_template(
        self,
        template_id: str,
        url: str,
        selectors: Dict[str, str],
        user_overrides: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> PipetConfiguration:
        """Create a scraping configuration from a template"""

        if template_id not in self.templates:
            raise ValidationError(f"Template not found: {template_id}")

        template = self.templates[template_id]

        # Start with default config from template
        config_data = template.default_config.copy()

        # Add required fields
        config_data["url"] = url
        config_data["selectors"] = selectors

        # Apply user overrides
        if user_overrides:
            config_data.update(user_overrides)

        # Set metadata
        config_data["request_id"] = request_id or str(hash(url + str(selectors)))
        config_data["model_version"] = "1.0"
        config_data["confidence_score"] = 0.8  # Default confidence

        # Create configuration
        try:
            config = PipetConfiguration(**config_data)

            # Update template usage
            template.usage_count += 1
            template.updated_at = datetime.now()
            self._save_templates()

            self.logger.info(
                "Created configuration from template",
                template_id=template_id,
                config_id=config.config_id,
                url=url
            )

            return config

        except Exception as e:
            raise ValidationError(f"Failed to create configuration: {str(e)}")

    def validate_configuration(
        self,
        config: PipetConfiguration,
        validation_level: ConfigValidationLevel = ConfigValidationLevel.BASIC
    ) -> Dict[str, Any]:
        """Validate a scraping configuration"""

        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "validation_level": validation_level.value
        }

        # Basic validation
        if not config.url:
            validation_results["errors"].append("URL is required")
            validation_results["is_valid"] = False
        elif not (config.url.startswith("http://") or config.url.startswith("https://")):
            validation_results["errors"].append("URL must start with http:// or https://")
            validation_results["is_valid"] = False

        if not config.selectors:
            validation_results["errors"].append("At least one selector is required")
            validation_results["is_valid"] = False

        # Strict validation
        if validation_level in [ConfigValidationLevel.STRICT, ConfigValidationLevel.PRODUCTION]:
            # Validate timeout
            if config.timeout < 1 or config.timeout > 300:
                validation_results["errors"].append("Timeout must be between 1 and 300 seconds")
                validation_results["is_valid"] = False

            # Validate retry config
            if config.retry_config.max_retries > 10:
                validation_results["warnings"].append("High retry count may cause long delays")

            if config.retry_config.retry_delay < 0.1:
                validation_results["warnings"].append("Very short retry delay may overwhelm target server")

            # Validate rate limiting
            if config.rate_limiting.requests_per_second > 10:
                validation_results["warnings"].append("High request rate may trigger anti-scraping measures")

        # Production validation
        if validation_level == ConfigValidationLevel.PRODUCTION:
            # Check for production readiness
            if not config.output_file:
                validation_results["recommendations"].append("Consider setting output_file for production")

            if config.confidence_score < 0.7:
                validation_results["recommendations"].append("Low confidence score - review configuration")

            if not config.data_transformations:
                validation_results["recommendations"].append("Consider adding data transformations for quality")

        return validation_results

    def optimize_configuration(
        self,
        config: PipetConfiguration,
        optimization_goals: Optional[List[str]] = None
    ) -> ConfigOptimization:
        """Optimize a scraping configuration"""

        if not optimization_goals:
            optimization_goals = ["performance", "reliability", "efficiency"]

        # Start with original config
        optimized_config_data = config.dict()
        optimizations_applied = []

        # Performance optimizations
        if "performance" in optimization_goals:
            # Adjust timeout based on typical response times
            if config.timeout > 60:
                optimized_config_data["timeout"] = 45
                optimizations_applied.append("Reduced timeout for better performance")

            # Optimize retry settings
            if config.retry_config.retry_delay > 3.0:
                optimized_config_data["retry_config"]["retry_delay"] = 2.0
                optimizations_applied.append("Optimized retry delay for faster recovery")

        # Reliability optimizations
        if "reliability" in optimization_goals:
            # Increase retry count for reliability
            if config.retry_config.max_retries < 3:
                optimized_config_data["retry_config"]["max_retries"] = 3
                optimizations_applied.append("Increased retry count for better reliability")

            # Add user agent if missing
            if "User-Agent" not in config.headers:
                optimized_config_data["headers"]["User-Agent"] = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                optimizations_applied.append("Added User-Agent header for compatibility")

        # Efficiency optimizations
        if "efficiency" in optimization_goals:
            # Adjust rate limiting
            if config.rate_limiting.requests_per_second < 0.5:
                optimized_config_data["rate_limiting"]["requests_per_second"] = 1.0
                optimizations_applied.append("Increased request rate for better efficiency")

            # Remove unnecessary headers
            unnecessary_headers = ["Connection", "Pragma"]
            for header in unnecessary_headers:
                if header in optimized_config_data["headers"]:
                    del optimized_config_data["headers"][header]
                    optimizations_applied.append(f"Removed unnecessary header: {header}")

        # Create optimized configuration
        try:
            optimized_config = PipetConfiguration(**optimized_config_data)

            # Calculate performance improvements (estimates)
            performance_improvement = {
                "estimated_time_reduction": 10.0,  # percentage
                "estimated_reliability_increase": 15.0,  # percentage
                "estimated_efficiency_gain": 8.0  # percentage
            }

            # Validation results
            validation_results = self.validate_configuration(
                optimized_config,
                ConfigValidationLevel.STRICT
            )

            optimization = ConfigOptimization(
                config_id=config.config_id,
                original_config=config,
                optimized_config=optimized_config,
                optimization_applied=optimizations_applied,
                performance_improvement=performance_improvement,
                validation_results=validation_results,
                optimization_timestamp=datetime.now()
            )

            # Cache optimization result
            self.optimization_cache[config.config_id] = optimization

            self.logger.info(
                "Optimized configuration",
                config_id=config.config_id,
                optimizations_applied=len(optimizations_applied)
            )

            return optimization

        except Exception as e:
            raise ValidationError(f"Failed to create optimized configuration: {str(e)}")

    def get_template_by_type(self, template_type: ConfigTemplateType) -> List[ConfigTemplate]:
        """Get templates by type"""
        return [
            template for template in self.templates.values()
            if template.template_type == template_type
        ]

    def suggest_template(
        self,
        url: str,
        description: Optional[str] = None
    ) -> Optional[ConfigTemplate]:
        """Suggest appropriate template based on URL and description"""

        url_lower = url.lower()
        description_lower = (description or "").lower()

        # Check for economic data indicators
        economic_keywords = ["economy", "gdp", "inflation", "employment", "interest", "central", "bank", "government"]
        if any(keyword in url_lower or keyword in description_lower for keyword in economic_keywords):
            economic_templates = self.get_template_by_type(ConfigTemplateType.ECONOMIC_DATA)
            return economic_templates[0] if economic_templates else None

        # Check for market data indicators
        market_keywords = ["market", "stock", "price", "trading", "finance", "quote", "ticker"]
        if any(keyword in url_lower or keyword in description_lower for keyword in market_keywords):
            market_templates = self.get_template_by_type(ConfigTemplateType.MARKET_DATA)
            return market_templates[0] if market_templates else None

        # Check for government data indicators
        gov_keywords = ["gov", "government", "census", "statistics", "bureau", "department"]
        if any(keyword in url_lower or keyword in description_lower for keyword in gov_keywords):
            gov_templates = self.get_template_by_type(ConfigTemplateType.GOVERNMENT_STATS)
            if gov_templates:
                return gov_templates[0]
            else:
                # Fall back to economic data template
                economic_templates = self.get_template_by_type(ConfigTemplateType.ECONOMIC_DATA)
                return economic_templates[0] if economic_templates else None

        # Default to economic data template
        economic_templates = self.get_template_by_type(ConfigTemplateType.ECONOMIC_DATA)
        return economic_templates[0] if economic_templates else None

    def create_batch_configuration(
        self,
        batch_request: BatchRequest,
        template_id: Optional[str] = None
    ) -> List[PipetConfiguration]:
        """Create configurations for a batch request"""

        configurations = []

        for i, natural_request in enumerate(batch_request.requests):
            try:
                # Determine template to use
                effective_template_id = template_id

                if not effective_template_id:
                    # Suggest template based on request
                    suggested_template = self.suggest_template(
                        "",  # URL not available in natural request
                        natural_request.user_description
                    )
                    effective_template_id = suggested_template.template_id if suggested_template else "economic_data_default"

                # Extract URL and selectors from NLP processing result or user description
                # This is a simplified implementation - in practice, you'd get this from NLP processing
                url = "extracted_url_from_nlp"  # Placeholder
                selectors = {"data": "extracted_selector_from_nlp"}  # Placeholder

                # Create configuration
                config = self.create_configuration_from_template(
                    template_id=effective_template_id,
                    url=url,
                    selectors=selectors,
                    request_id=natural_request.request_id
                )

                configurations.append(config)

            except Exception as e:
                self.logger.error(
                    "Failed to create configuration for batch request",
                    request_id=natural_request.request_id,
                    error=str(e)
                )
                # Continue with other requests
                continue

        # Update batch request with configurations
        batch_request.configurations = configurations

        self.logger.info(
            "Created batch configurations",
            batch_id=batch_request.batch_id,
            total_requests=len(batch_request.requests),
            successful_configs=len(configurations)
        )

        return configurations

    def export_configuration(
        self,
        config: PipetConfiguration,
        export_format: str = "json",
        file_path: Optional[str] = None
    ) -> str:
        """Export configuration to file"""

        if export_format.lower() == "json":
            config_data = config.json(indent=2, ensure_ascii=False)
        else:
            raise ValidationError(f"Unsupported export format: {export_format}")

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(config_data)

                self.logger.info(
                    "Exported configuration",
                    config_id=config.config_id,
                    file_path=file_path,
                    format=export_format
                )

            except Exception as e:
                raise ConfigurationError(f"Failed to export configuration: {str(e)}")

        return config_data

    def import_configuration(
        self,
        config_data: Union[str, Dict[str, Any]],
        config_format: str = "json"
    ) -> PipetConfiguration:
        """Import configuration from data"""

        try:
            if config_format.lower() == "json":
                if isinstance(config_data, str):
                    config_dict = json.loads(config_data)
                else:
                    config_dict = config_data
            else:
                raise ValidationError(f"Unsupported import format: {config_format}")

            config = PipetConfiguration(**config_dict)

            self.logger.info(
                "Imported configuration",
                config_id=config.config_id,
                format=config_format
            )

            return config

        except Exception as e:
            raise ValidationError(f"Failed to import configuration: {str(e)}")

    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get template usage statistics"""

        stats = {
            "total_templates": len(self.templates),
            "template_usage": {},
            "most_used_template": None,
            "average_success_rate": 0.0
        }

        if self.templates:
            total_usage = sum(template.usage_count for template in self.templates.values())
            total_success_rate = sum(template.success_rate for template in self.templates.values())

            stats["average_success_rate"] = total_success_rate / len(self.templates)

            # Find most used template
            most_used_template = max(
                self.templates.values(),
                key=lambda t: t.usage_count
            )
            stats["most_used_template"] = {
                "template_id": most_used_template.template_id,
                "name": most_used_template.name,
                "usage_count": most_used_template.usage_count
            }

            # Individual template stats
            for template_id, template in self.templates.items():
                stats["template_usage"][template_id] = {
                    "name": template.name,
                    "usage_count": template.usage_count,
                    "success_rate": template.success_rate,
                    "type": template.template_type.value
                }

        return stats

    def cleanup_cache(self, max_age_days: int = 30) -> None:
        """Clean up old cached configurations and optimizations"""

        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        # Clean up optimization cache
        expired_optimizations = [
            key for key, opt in self.optimization_cache.items()
            if opt.optimization_timestamp < cutoff_date
        ]

        for key in expired_optimizations:
            del self.optimization_cache[key]

        self.logger.info(
            "Cleaned up optimization cache",
            removed_count=len(expired_optimizations),
            max_age_days=max_age_days
        )