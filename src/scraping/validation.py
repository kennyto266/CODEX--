"""
Data validation utilities for configuration and data quality checks

Provides comprehensive validation for pipet configurations, scraped data,
and quality assessment metrics.
"""

import json
import yaml
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse

from .models import (
    PipetConfiguration, ScrapedDataRecord, DataQualityReport,
    QualityConfig, NLPProcessingResult, ScrapingExecution
)
from .exceptions import ValidationError, DataQualityError
from .logging_config import StructuredLogger


class ConfigurationValidator:
    """Validator for pipet configurations"""

    def __init__(self):
        self.logger = StructuredLogger("scraping.validation")

    def validate_config(self, config: PipetConfiguration) -> Dict[str, Any]:
        """
        Validate a pipet configuration

        Args:
            config: Pipet configuration to validate

        Returns:
            Validation result with status and issues

        Raises:
            ValidationError: If configuration is invalid
        """
        validation_result = {
            "is_valid": True,
            "validation_score": 1.0,
            "issues": [],
            "warnings": [],
            "suggestions": []
        }

        try:
            # URL validation
            self._validate_url(config.url, validation_result)

            # Selector validation
            self._validate_selectors(config.selectors, validation_result)

            # Output configuration validation
            self._validate_output_config(config, validation_result)

            # Timeout and retry validation
            self._validate_execution_config(config, validation_result)

            # Calculate overall score
            validation_result["validation_score"] = max(0.0, 1.0 - len(validation_result["issues"]) * 0.2)

            # Check if valid enough for execution
            if validation_result["issues"]:
                validation_result["is_valid"] = False

        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Validation error: {str(e)}")

        self.logger.info(
            f"Configuration validation completed",
            config_id=config.config_id,
            is_valid=validation_result["is_valid"],
            score=validation_result["validation_score"],
            issues_count=len(validation_result["issues"]),
            warnings_count=len(validation_result["warnings"]),
            operation="validate_config"
        )

        return validation_result

    def _validate_url(self, url: str, result: Dict[str, Any]) -> None:
        """Validate URL"""
        if not url:
            result["issues"].append("URL is required")
            return

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                result["issues"].append(f"Invalid URL format: {url}")
                return

            if parsed.scheme not in ["http", "https"]:
                result["warnings"].append(f"Non-standard URL scheme: {parsed.scheme}")

            # Check for potentially problematic URLs
            if parsed.netloc in ["localhost", "127.0.0.1"]:
                result["warnings"].append("Localhost URL may not work in production")

        except Exception as e:
            result["issues"].append(f"URL parsing error: {str(e)}")

    def _validate_selectors(self, selectors: Dict[str, str], result: Dict[str, Any]) -> None:
        """Validate CSS selectors"""
        if not selectors:
            result["issues"].append("At least one selector is required")
            return

        invalid_selectors = []
        for field_name, selector in selectors.items():
            if not selector or not selector.strip():
                invalid_selectors.append(f"{field_name}: empty selector")
                continue

            # Basic CSS selector validation
            try:
                # This is a basic check - in practice, you'd want more sophisticated validation
                if not re.match(r'^[a-zA-Z0-9_\-\s\[\].*>+$', selector):
                    result["warnings"].append(f"{field_name}: selector may contain invalid characters: {selector}")
            except Exception as e:
                invalid_selectors.append(f"{field_name}: selector validation error: {str(e)}")

        if invalid_selectors:
            result["issues"].extend(invalid_selectors)

    def _validate_output_config(self, config: PipetConfiguration, result: Dict[str, Any]) -> None:
        """Validate output configuration"""
        # Output format validation
        valid_formats = ["json", "csv", "xml", "yaml"]
        if config.output_format.value not in valid_formats:
            result["issues"].append(f"Invalid output format: {config.output_format.value}")

        # Output file validation (if specified)
        if config.output_file:
            try:
                output_path = config.output_file
                output_dir = str(Path(output_path).parent)

                # Check if directory exists or can be created
                if not Path(output_dir).exists():
                    result["warnings"].append(f"Output directory does not exist: {output_dir}")

                # Check file extension matches format
                extension_map = {
                    "json": ".json",
                    "csv": ".csv",
                    "xml": ".xml",
                    "yaml": ".yaml"
                }
                expected_ext = extension_map.get(config.output_format.value)
                if expected_ext and not config.output_file.endswith(expected_ext):
                    result["warnings"].append(f"File extension doesn't match format: {config.output_file}")

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
        if config.retry_config.max_retries > 5:
            result["warnings"].append("High retry count may cause performance issues")

        if config.retry_config.retry_delay < 0.1:
            result["issues"].append("Retry delay must be at least 0.1 seconds")
        elif config.retry_config.retry_delay > 60:
            result["warnings"].append("Long retry delay may cause poor user experience")

        if config.retry_config.backoff_factor < 1.0:
            result["issues"].append("Backoff factor must be at least 1.0")


class DataQualityValidator:
    """Validator for scraped data quality"""

    def __init__(self, config: Optional[QualityConfig] = None):
        self.logger = StructuredLogger("scraping.quality")
        self.config = config

    def validate_scraped_data(
        self,
        data_records: List[ScrapedDataRecord],
        execution_id: str
    ) -> DataQualityReport:
        """
        Validate scraped data quality

        Args:
            data_records: List of scraped data records
            execution_id: Execution identifier

        Returns:
            DataQualityReport with quality assessment
        """
        report = DataQualityReport(
            execution_id=execution_id,
            overall_quality_score=0.0,
            completeness_score=0.0,
            accuracy_score=0.0,
            consistency_score=0.0,
            timeliness_score=0.0
        )

        if not data_records:
            report.overall_quality_score = 0.0
            report.quality_issues.append(
                QualityIssue(
                    severity="critical",
                    issue_type="missing",
                    field_name="all",
                    description="No data records found",
                    affected_records=0,
                    suggested_fix="Check pipet configuration and website accessibility"
                )
            )
            return report

        # Calculate quality metrics
        report.completeness_score = self._calculate_completeness(data_records)
        report.accuracy_score = self._calculate_accuracy(data_records)
        report.consistency_score = self._calculate_consistency(data_records)
        report.timeliness_score = self._calculate_timeliness(data_records)

        # Calculate overall score
        scores = [
            report.completeness_score,
            report.accuracy_score,
            report.consistency_score,
            report.timeliness_score
        ]
        report.overall_quality_score = sum(scores) / len(scores)

        # Identify quality issues
        report.quality_issues = self._identify_quality_issues(
            data_records,
            report.completeness_score,
            report.accuracy_score,
            report.consistency_score,
            report.timeliness_score
        )

        # Add recommendations
        report.recommendations = self._generate_recommendations(report)

        self.logger.info(
            f"Data quality validation completed",
            execution_id=execution_id,
            records_count=len(data_records),
            overall_score=report.overall_quality_score,
            completeness=report.complepleteness_score,
            accuracy=report.accuracy_score,
            consistency=report.consistency_score,
            timeliness=report.timeliness_score,
            issues_count=len(report.quality_issues),
            operation="validate_scraped_data"
        )

        return report

    def _calculate_completeness(self, data_records: List[ScrapedDataRecord]) -> float:
        """Calculate data completeness score"""
        if not data_records:
            return 0.0

        # Check for required fields
        required_fields = ["source_url", "data_fields"]
        complete_records = 0

        for record in data_records:
            is_complete = True
            for field in required_fields:
                if not hasattr(record, field) or getattr(record, field) is None:
                    is_complete = False
                    break
            if is_complete:
                complete_records += 1

        return complete_records / len(data_records)

    def _calculate_accuracy(self, data_records: List[ScrapedDataRecord]) -> float:
        """Calculate data accuracy score"""
        if not data_records:
            return 0.0

        # Check data types and formats
        accuracy_scores = []

        for record in data_records:
            score = 1.0

            # Check data fields structure
            if not record.data_fields or not isinstance(record.data_fields, dict):
                score *= 0.5
            else:
                # Check for empty values
                total_fields = len(record.data_fields)
                empty_fields = sum(1 for v in record.data_fields.values() if not v)
                if total_fields > 0:
                    score *= (total_fields - empty_fields) / total_fields

            accuracy_scores.append(score)

        return sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0

    def _calculate_consistency(self, data_records: List[ScrapedDataRecord]) -> float:
        """Calculate data consistency score"""
        if len(data_records) < 2:
            return 1.0  # Consistency is perfect with 0 or 1 records

        consistency_scores = []

        # Check field consistency across records
        if data_records:
            first_record = data_records[0]
            field_names = set(first_record.data_fields.keys())

            for record in data_records[1:]:
                current_fields = set(record.data_fields.keys())
                intersection = len(field_names.intersection(current_fields))
                union = len(field_names.union(current_fields))

                if union > 0:
                    consistency_scores.append(intersection / union)

        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0

    def _calculate_timeliness(self, data_records: List[ScrapedDataRecord]) -> float:
        """Calculate data timeliness score"""
        if not data_records:
            return 1.0

        now = datetime.now()
        timeliness_scores = []

        for record in data_records:
            record_time = record.extraction_timestamp
            time_diff = (now - record_time).total_seconds()

            # Score based on data freshness (newer is better)
            # 1.0 = 0-1 hour old, 0.8 = 1-24 hours old, 0.6 = 1-7 days old, 0.4 = 1-30 days old, 0.2 = >30 days old
            if time_diff < 3600:  # < 1 hour
                score = 1.0
            elif time_diff < 86400:  # < 1 day
                score = 0.8
            elif time_diff < 604800:  # < 1 week
                score = 0.6
            elif time_diff < 2592000:  # < 30 days
                score = 0.4
            else:  # > 30 days
                score = 0.2

            timeliness_scores.append(score)

        return sum(timeliness_scores) / len(timeliness_scores)

    def _identify_quality_issues(
        self,
        data_records: List[ScrapedDataRecord],
        completeness_score: float,
        accuracy_score: float,
        consistency_score: float,
        timeliness_score: float
    ) -> List[QualityIssue]:
        """Identify quality issues in the data"""
        issues = []

        # Completeness issues
        if completeness_score < 0.9:
            missing_records = len(data_records) - int(len(data_records) * completeness_score)
            issues.append(QualityIssue(
                severity="high" if completeness_score < 0.7 else "medium",
                issue_type="missing",
                field_name="data_records",
                description=f"Missing or incomplete data in {missing_records} records",
                affected_records=missing_records,
                suggested_fix="Improve data extraction selectors"
            ))

        # Accuracy issues
        if accuracy_score < 0.9:
            issues.append(QualityIssue(
                severity="high" if accuracy_score < 0.7 else "medium",
                issue_type="inaccurate",
                field_name="data_fields",
                description=f"Data accuracy issues detected (score: {accuracy_score:.2f})",
                affected_records=int(len(data_records) * (1 - accuracy_score)),
                suggested_fix="Review extraction rules and data cleaning"
            ))

        # Consistency issues
        if consistency_score < 0.9:
            issues.append(QualityIssue(
                severity="medium",
                issue_type="inconsistent",
                field_name="data_fields",
                description=f"Inconsistent field structure across records (score: {consistency_score:.2f})",
                affected_records=int(len(data_records) * (1 - consistency_score)),
                suggested_fix="Standardize data extraction format"
            ))

        # Timeliness issues
        if timeliness_score < 0.8:
            issues.append(QualityIssue(
                severity="low",
                issue_type="timeliness",
                field_name="extraction_timestamp",
                description=f"Data may be outdated (score: {timeliness_score:.2f})",
                affected_records=int(len(data_records) * (1 - timeliness_score)),
                suggested_fix="Schedule more frequent data refresh"
            ))

        return issues

    def _generate_recommendations(self, report: DataQualityReport) -> List[str]:
        """Generate improvement recommendations based on quality assessment"""
        recommendations = []

        if report.completeness_score < 0.9:
            recommendations.append("Improve data extraction selectors to capture all required fields")
            recommendations.append("Check website structure changes and update extraction rules")

        if report.accuracy_score < 0.9:
            recommendations.append("Review and refine CSS selectors for better data extraction")
            recommendations.append("Add data cleaning and validation steps")

        if report.consistency_score < 0.9:
            recommendations.append("Standardize data format across all extraction rules")
            recommendations.append("Implement field mapping and normalization")

        if report.timeliness_score < 0.8:
            recommendations.append("Increase scraping frequency for time-sensitive data")
            recommendations.append("Implement change detection to trigger updates")

        return recommendations


# Global instances
config_validator = ConfigurationValidator()
data_validator = DataQualityValidator()


def validate_configuration(config: PipetConfiguration) -> Dict[str, Any]:
    """Validate a pipet configuration"""
    return config_validator.validate_config(config)


def validate_scraped_data(data_records: List[ScrapedDataRecord], execution_id: str) -> DataQualityReport:
    """Validate scraped data quality"""
    return data_validator.validate_scraped_data(data_records, execution_id)