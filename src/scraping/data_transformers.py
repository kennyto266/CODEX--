"""
Data transformation utilities for scraped data

Provides comprehensive data cleaning, normalization, and transformation
capabilities for various data types and formats.
"""

import re
import json
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import pandas as pd
import numpy as np

from .models import ScrapedDataRecord
from .logging_config import StructuredLogger


class DataTransformer:
    """Comprehensive data transformation utilities"""

    def __init__(self):
        self.logger = StructuredLogger("scraping.data_transformers")

        # Initialize transformation rules
        self.cleaning_rules = self._load_cleaning_rules()
        self.conversion_rules = self._load_conversion_rules()
        self.validation_rules = self._load_validation_rules()

    def transform_record(
        self,
        record: ScrapedDataRecord,
        transformation_config: Optional[Dict[str, Any]] = None
    ) -> ScrapedDataRecord:
        """
        Transform a single scraped data record

        Args:
            record: Scraped data record to transform
            transformation_config: Configuration for transformations

        Returns:
            Transformed data record
        """
        try:
            self.logger.debug(
                f"Transforming record",
                record_id=record.record_id,
                execution_id=record.execution_id,
                fields_count=len(record.data_fields),
                operation="transform_record"
            )

            transformed_data = {}
            transformed_metadata = {}

            # Apply transformations to each field
            for field_name, field_value in record.data_fields.items():
                try:
                    transformed_value, field_metadata = self._transform_field(
                        field_name,
                        field_value,
                        transformation_config
                    )
                    transformed_data[field_name] = transformed_value
                    transformed_metadata[field_name] = field_metadata

                except Exception as e:
                    self.logger.warning(
                        f"Field transformation failed",
                        record_id=record.record_id,
                        field_name=field_name,
                        error=str(e),
                        operation="transform_field"
                    )
                    # Keep original value if transformation fails
                    transformed_data[field_name] = field_value
                    transformed_metadata[field_name] = {
                        "transformation_status": "failed",
                        "error": str(e)
                    }

            # Create transformed record
            transformed_record = ScrapedDataRecord(
                record_id=record.record_id,
                execution_id=record.execution_id,
                source_url=record.source_url,
                data_fields=transformed_data,
                extraction_timestamp=record.extraction_timestamp,
                field_metadata=transformed_metadata,
                quality_score=record.quality_score
            )

            self.logger.debug(
                f"Record transformation completed",
                record_id=record.record_id,
                operation="transform_record"
            )

            return transformed_record

        except Exception as e:
            self.logger.error(
                f"Record transformation failed: {str(e)}",
                record_id=record.record_id,
                operation="transform_record"
            )
            raise

    def _transform_field(
        self,
        field_name: str,
        field_value: Any,
        config: Optional[Dict[str, Any]] = None
    ) -> Tuple[Any, Dict[str, Any]]:
        """Transform individual field"""
        metadata = {
            "original_value": field_value,
            "transformation_status": "success",
            "cleaning_applied": [],
            "conversions_applied": []
        }

        if field_value is None or field_value == "":
            return None, metadata

        # Convert to string for processing
        if not isinstance(field_value, str):
            field_value = str(field_value)

        # Apply cleaning rules
        cleaned_value = self._apply_cleaning_rules(field_name, field_value, metadata)

        # Apply conversion rules
        converted_value = self._apply_conversion_rules(field_name, cleaned_value, metadata)

        # Apply validation
        validation_result = self._apply_validation_rules(field_name, converted_value, metadata)

        metadata["validation_result"] = validation_result

        return converted_value, metadata

    def _apply_cleaning_rules(self, field_name: str, value: str, metadata: Dict[str, Any]) -> str:
        """Apply data cleaning rules"""
        cleaned_value = value

        # Basic whitespace cleaning
        if "strip_whitespace" in self.cleaning_rules.get(field_name, ["strip_whitespace"]):
            cleaned_value = cleaned_value.strip()
            metadata["cleaning_applied"].append("strip_whitespace")

        # Remove extra whitespace
        if "normalize_whitespace" in self.cleaning_rules.get(field_name, []):
            cleaned_value = re.sub(r'\s+', ' ', cleaned_value)
            metadata["cleaning_applied"].append("normalize_whitespace")

        # Remove special characters based on field type
        if self._is_numeric_field(field_name):
            # Remove common numeric formatting characters
            cleaned_value = self._clean_numeric_field(cleaned_value, metadata)

        elif self._is_date_field(field_name):
            # Clean date fields
            cleaned_value = self._clean_date_field(cleaned_value, metadata)

        else:
            # Clean text fields
            cleaned_value = self._clean_text_field(cleaned_value, metadata)

        return cleaned_value

    def _clean_numeric_field(self, value: str, metadata: Dict[str, Any]) -> str:
        """Clean numeric field values"""
        original_value = value

        # Remove common prefixes and suffixes
        patterns_to_remove = [
            r'^[HK\$USD$€£]+',  # Currency symbols
            r'[,，]',  # Thousand separators
            r'%$',  # Percent sign at end
            r'^\+\-?',  # Leading plus/minus signs (keep for now)
        ]

        for pattern in patterns_to_remove:
            if re.search(pattern, value):
                value = re.sub(pattern, '', value)
                metadata["cleaning_applied"].append(f"remove_pattern_{pattern}")

        # Handle parentheses for negative numbers
        if value.startswith('(') and value.endswith(')'):
            value = '-' + value[1:-1]
            metadata["cleaning_applied"].append("parentheses_to_negative")

        return value.strip()

    def _clean_date_field(self, value: str, metadata: Dict[str, Any]) -> str:
        """Clean date field values"""
        original_value = value

        # Common date separators to normalize
        separator_replacements = {
            '年': '-',
            '月': '-',
            '日': '',
            '/': '-',
            '.': '-',
            ' ': '-'
        }

        for old_sep, new_sep in separator_replacements.items():
            if old_sep in value:
                value = value.replace(old_sep, new_sep)
                metadata["cleaning_applied"].append(f"replace_separator_{old_sep}")

        # Remove extra separators
        value = re.sub(r'-+', '-', value)
        value = value.strip('-')

        return value

    def _clean_text_field(self, value: str, metadata: Dict[str, Any]) -> str:
        """Clean text field values"""
        # Remove non-printable characters except common ones
        value = re.sub(r'[^\x20-\x7E\u4e00-\u9fff\u3400-\u4dbf]', '', value)
        metadata["cleaning_applied"].append("remove_non_printable")

        # Normalize quotes
        value = value.replace('"', '"').replace('"', '"')
        value = value.replace(''', "'").replace(''', "'")
        metadata["cleaning_applied"].append("normalize_quotes")

        return value

    def _apply_conversion_rules(self, field_name: str, value: str, metadata: Dict[str, Any]) -> Any:
        """Apply data type conversion rules"""
        if not value or value.strip() == "":
            return None

        conversion_rules = self.conversion_rules.get(field_name, [])

        for rule in conversion_rules:
            try:
                if rule == "convert_to_number":
                    converted_value = self._convert_to_number(value)
                    if converted_value is not None:
                        metadata["conversions_applied"].append("convert_to_number")
                        return converted_value

                elif rule == "convert_to_date":
                    converted_value = self._convert_to_date(value)
                    if converted_value is not None:
                        metadata["conversions_applied"].append("convert_to_date")
                        return converted_value

                elif rule == "convert_to_datetime":
                    converted_value = self._convert_to_datetime(value)
                    if converted_value is not None:
                        metadata["conversions_applied"].append("convert_to_datetime")
                        return converted_value

                elif rule == "convert_to_boolean":
                    converted_value = self._convert_to_boolean(value)
                    if converted_value is not None:
                        metadata["conversions_applied"].append("convert_to_boolean")
                        return converted_value

            except Exception as e:
                self.logger.warning(
                    f"Conversion rule failed",
                    field_name=field_name,
                    rule=rule,
                    value=value,
                    error=str(e),
                    operation="apply_conversion_rules"
                )
                continue

        # Default: return as string
        return value

    def _convert_to_number(self, value: str) -> Optional[Union[int, float, Decimal]]:
        """Convert string to numeric value"""
        try:
            # Try integer first
            if '.' not in value and 'e' not in value.lower():
                return int(value)

            # Try float
            float_val = float(value)

            # Check if it's effectively an integer
            if float_val.is_integer():
                return int(float_val)

            # Use Decimal for precision
            return Decimal(str(float_val))

        except (ValueError, InvalidOperation):
            # Try removing any remaining non-numeric characters
            numeric_only = re.sub(r'[^\d\.\-+eE]', '', value)
            if numeric_only and numeric_only != value:
                return self._convert_to_number(numeric_only)

            return None

    def _convert_to_date(self, value: str) -> Optional[date]:
        """Convert string to date object"""
        date_formats = [
            '%Y-%m-%d',      # 2024-01-15
            '%Y/%m/%d',      # 2024/01/15
            '%d-%m-%Y',      # 15-01-2024
            '%d/%m/%Y',      # 15/01/2024
            '%Y年%m月%d日',   # 2024年1月15日
            '%Y%m%d',        # 20240115
            '%d-%b-%Y',      # 15-Jan-2024
            '%Y-%b-%d',      # 2024-Jan-15
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        # Try pandas date parsing for more flexible formats
        try:
            return pd.to_datetime(value).date()
        except:
            pass

        return None

    def _convert_to_datetime(self, value: str) -> Optional[datetime]:
        """Convert string to datetime object"""
        datetime_formats = [
            '%Y-%m-%d %H:%M:%S',    # 2024-01-15 14:30:00
            '%Y-%m-%d %H:%M',       # 2024-01-15 14:30
            '%Y/%m/%d %H:%M:%S',    # 2024/01/15 14:30:00
            '%d-%m-%Y %H:%M:%S',    # 15-01-2024 14:30:00
        ]

        for fmt in datetime_formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        # Try pandas datetime parsing
        try:
            return pd.to_datetime(value)
        except:
            pass

        return None

    def _convert_to_boolean(self, value: str) -> Optional[bool]:
        """Convert string to boolean value"""
        true_values = ['true', 'yes', 'y', '1', '是', '真', '對', 'enable', 'enabled', 'on']
        false_values = ['false', 'no', 'n', '0', '否', '假', '錯', 'disable', 'disabled', 'off']

        value_lower = value.lower().strip()

        if value_lower in true_values:
            return True
        elif value_lower in false_values:
            return False

        return None

    def _apply_validation_rules(self, field_name: str, value: Any, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Apply validation rules to transformed value"""
        validation_result = {
            "is_valid": True,
            "validation_errors": [],
            "validation_warnings": []
        }

        validation_rules = self.validation_rules.get(field_name, {})

        # Type validation
        expected_type = validation_rules.get("type")
        if expected_type and value is not None:
            if expected_type == "numeric" and not isinstance(value, (int, float, Decimal)):
                validation_result["is_valid"] = False
                validation_result["validation_errors"].append(f"Expected numeric value, got {type(value)}")
            elif expected_type == "date" and not isinstance(value, date) and not isinstance(value, datetime):
                validation_result["is_valid"] = False
                validation_result["validation_errors"].append(f"Expected date value, got {type(value)}")

        # Range validation for numeric values
        if isinstance(value, (int, float, Decimal)):
            min_value = validation_rules.get("min_value")
            max_value = validation_rules.get("max_value")

            if min_value is not None and value < min_value:
                validation_result["validation_warnings"].append(f"Value {value} below minimum {min_value}")

            if max_value is not None and value > max_value:
                validation_result["validation_warnings"].append(f"Value {value} above maximum {max_value}")

        # Non-empty validation
        if validation_rules.get("required", False) and (value is None or value == ""):
            validation_result["is_valid"] = False
            validation_result["validation_errors"].append("Required field is empty")

        return validation_result

    def transform_batch(
        self,
        records: List[ScrapedDataRecord],
        transformation_config: Optional[Dict[str, Any]] = None
    ) -> List[ScrapedDataRecord]:
        """
        Transform multiple data records

        Args:
            records: List of scraped data records
            transformation_config: Configuration for transformations

        Returns:
            List of transformed records
        """
        self.logger.info(
            f"Starting batch transformation",
            records_count=len(records),
            operation="transform_batch"
        )

        transformed_records = []
        transformation_stats = {
            "total_records": len(records),
            "successful_transformations": 0,
            "failed_transformations": 0,
            "field_transformations": 0
        }

        for record in records:
            try:
                transformed_record = self.transform_record(record, transformation_config)
                transformed_records.append(transformed_record)
                transformation_stats["successful_transformations"] += 1
                transformation_stats["field_transformations"] += len(record.data_fields)

            except Exception as e:
                self.logger.error(
                    f"Record transformation failed: {str(e)}",
                    record_id=record.record_id,
                    operation="transform_batch"
                )
                # Keep original record if transformation fails
                transformed_records.append(record)
                transformation_stats["failed_transformations"] += 1

        self.logger.info(
            f"Batch transformation completed",
            successful=transformation_stats["successful_transformations"],
            failed=transformation_stats["failed_transformations"],
            operation="transform_batch"
        )

        return transformed_records

    def transform_to_dataframe(
        self,
        records: List[ScrapedDataRecord],
        transformation_config: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Transform records to pandas DataFrame

        Args:
            records: List of scraped data records
            transformation_config: Configuration for transformations

        Returns:
            Transformed pandas DataFrame
        """
        # Transform records first
        transformed_records = self.transform_batch(records, transformation_config)

        # Extract data fields
        data_list = []
        for record in transformed_records:
            row_data = record.data_fields.copy()
            row_data.update({
                "record_id": record.record_id,
                "execution_id": record.execution_id,
                "source_url": record.source_url,
                "extraction_timestamp": record.extraction_timestamp,
                "quality_score": record.quality_score
            })
            data_list.append(row_data)

        # Create DataFrame
        df = pd.DataFrame(data_list)

        # Apply DataFrame-specific transformations
        df = self._transform_dataframe(df, transformation_config)

        return df

    def _transform_dataframe(self, df: pd.DataFrame, config: Optional[Dict[str, Any]]) -> pd.DataFrame:
        """Apply DataFrame-specific transformations"""
        # Sort by date column if available
        date_columns = [col for col in df.columns if 'date' in col.lower()]
        if date_columns:
            df = df.sort_values(date_columns[0])

        # Remove duplicates if specified
        if config and config.get("remove_duplicates", False):
            df = df.drop_duplicates()

        # Handle missing values
        if config:
            missing_value_strategy = config.get("missing_values", "keep")
            if missing_value_strategy == "drop":
                df = df.dropna()
            elif missing_value_strategy == "fill":
                fill_value = config.get("fill_value", 0)
                df = df.fillna(fill_value)

        return df

    def export_to_format(
        self,
        records: List[ScrapedDataRecord],
        output_format: str,
        output_path: str,
        transformation_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Export transformed records to specified format

        Args:
            records: List of scraped data records
            output_format: Output format (json, csv, excel, parquet)
            output_path: Output file path
            transformation_config: Configuration for transformations

        Returns:
            True if export successful, False otherwise
        """
        try:
            self.logger.info(
                f"Exporting data",
                records_count=len(records),
                output_format=output_format,
                output_path=output_path,
                operation="export_to_format"
            )

            # Transform records to DataFrame
            df = self.transform_to_dataframe(records, transformation_config)

            # Export based on format
            if output_format.lower() == "json":
                df.to_json(output_path, orient='records', date_format='iso', force_ascii=False, indent=2)
            elif output_format.lower() == "csv":
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif output_format.lower() in ["excel", "xlsx"]:
                df.to_excel(output_path, index=False)
            elif output_format.lower() == "parquet":
                df.to_parquet(output_path, index=False)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

            self.logger.info(
                f"Data export completed",
                output_path=output_path,
                records_count=len(df),
                operation="export_to_format"
            )

            return True

        except Exception as e:
            self.logger.error(
                f"Data export failed: {str(e)}",
                output_path=output_path,
                operation="export_to_format"
            )
            return False

    def _is_numeric_field(self, field_name: str) -> bool:
        """Check if field is numeric based on name"""
        numeric_keywords = [
            "rate", "amount", "value", "price", "index", "ratio", "percentage",
            "growth", "change", "number", "count", "volume", "quantity"
        ]
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in numeric_keywords)

    def _is_date_field(self, field_name: str) -> bool:
        """Check if field is date based on name"""
        date_keywords = ["date", "time", "timestamp", "period", "month", "year", "day"]
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in date_keywords)

    def _load_cleaning_rules(self) -> Dict[str, List[str]]:
        """Load default cleaning rules"""
        return {
            "default": ["strip_whitespace", "normalize_whitespace"],
            "rate": ["strip_whitespace", "remove_percent_sign", "remove_currency"],
            "amount": ["strip_whitespace", "remove_currency"],
            "growth": ["strip_whitespace", "remove_percent_sign"],
            "date": ["strip_whitespace", "normalize_date_format"],
        }

    def _load_conversion_rules(self) -> Dict[str, List[str]]:
        """Load default conversion rules"""
        return {
            "rate": ["convert_to_number"],
            "amount": ["convert_to_number"],
            "growth": ["convert_to_number"],
            "value": ["convert_to_number"],
            "price": ["convert_to_number"],
            "index": ["convert_to_number"],
            "ratio": ["convert_to_number"],
            "percentage": ["convert_to_number"],
            "date": ["convert_to_date"],
            "time": ["convert_to_datetime"],
            "timestamp": ["convert_to_datetime"],
        }

    def _load_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load default validation rules"""
        return {
            "rate": {
                "type": "numeric",
                "min_value": 0.0,
                "max_value": 100.0,
                "required": True
            },
            "amount": {
                "type": "numeric",
                "min_value": 0.0,
                "required": True
            },
            "growth": {
                "type": "numeric",
                "min_value": -100.0,
                "max_value": 1000.0
            },
            "date": {
                "type": "date",
                "required": True
            },
            "value": {
                "type": "numeric",
                "required": True
            }
        }


# Convenience functions
def create_data_transformer() -> DataTransformer:
    """Create data transformer instance"""
    return DataTransformer()


def transform_record(
    record: ScrapedDataRecord,
    transformation_config: Optional[Dict[str, Any]] = None
) -> ScrapedDataRecord:
    """Transform a single data record"""
    transformer = DataTransformer()
    return transformer.transform_record(record, transformation_config)


def transform_to_dataframe(
    records: List[ScrapedDataRecord],
    transformation_config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """Transform records to DataFrame"""
    transformer = DataTransformer()
    return transformer.transform_to_dataframe(records, transformation_config)