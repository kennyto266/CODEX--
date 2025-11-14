"""
Natural Language Processing interface for converting user descriptions
into structured scraping configurations.

Provides comprehensive NLP capabilities including text understanding,
entity extraction, and configuration generation support.
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from .models import (
    NaturalLanguageRequest, NLPProcessingResult, ProcessingStatus
)
from .exceptions import NLPProcessingError
from .config import get_global_config
from .logging_config import StructuredLogger


class NLPInterface:
    """Natural Language Processing interface for scraping configuration generation"""

    def __init__(self, config=None):
        self.logger = StructuredLogger("scraping.nlp_interface")
        self.config = config or get_global_config()
        self.nlp_config = self.config.nlp_config

        # Initialize NLP model (would be transformer-based in production)
        self._model = None
        self._tokenizer = None

    async def process_request(self, request: NaturalLanguageRequest) -> NLPProcessingResult:
        """
        Process natural language request and extract scraping requirements

        Args:
            request: Natural language request from user

        Returns:
            NLP processing result with extracted information

        Raises:
            NLPProcessingError: If processing fails
        """
        start_time = datetime.now()
        request_id = request.request_id

        try:
            self.logger.info(
                f"Processing NLP request",
                request_id=request_id,
                description_length=len(request.user_description),
                operation="process_request"
            )

            # Validate input
            self._validate_request(request)

            # Preprocess text
            processed_text = self._preprocess_text(request.user_description)

            # Extract key information using NLP model
            nlp_result = await self._run_nlp_model(processed_text, request.user_context)

            # Post-process and structure results
            structured_result = await self._structure_nlp_result(
                request_id, nlp_result, request.user_context
            )

            # Validate processing result
            await self._validate_processing_result(structured_result)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            structured_result.processing_time = processing_time

            self.logger.info(
                f"NLP processing completed successfully",
                request_id=request_id,
                confidence_score=structured_result.confidence_score,
                urls_count=len(structured_result.extracted_urls),
                processing_time=processing_time,
                operation="process_request"
            )

            return structured_result

        except NLPProcessingError:
            raise
        except Exception as e:
            error_msg = f"NLP processing failed: {str(e)}"
            self.logger.error(
                error_msg,
                request_id=request_id,
                operation="process_request"
            )
            raise NLPProcessingError(error_msg, error_code="NLP_001")

    def _validate_request(self, request: NaturalLanguageRequest) -> None:
        """Validate natural language request"""
        if not request or not request.user_description:
            raise NLPProcessingError("Request description is required", error_code="NLP_002")

        if len(request.user_description.strip()) < 5:
            raise NLPProcessingError("Description too short", error_code="NLP_003")

        if len(request.user_description) > 2000:
            raise NLPProcessingError("Description too long (max 2000 characters)", error_code="NLP_004")

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for NLP processing"""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Convert to lowercase for processing while preserving original for output
        processed_text = text.lower()

        # Add spacing around URLs
        url_pattern = r'https?://[^\s]+'
        processed_text = re.sub(url_pattern, lambda m: f' {m.group()} ', processed_text)

        # Normalize common abbreviations
        abbreviations = {
            'hkma': '香港金管局',
            'hibor': 'hibor利率',
            'gdp': '國內生產總值',
            'cpi': '消費物價指數'
        }

        for abbr, full in abbreviations.items():
            processed_text = processed_text.replace(abbr, full)

        return processed_text

    async def _run_nlp_model(self, processed_text: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run NLP model to extract structured information

        Args:
            processed_text: Preprocessed text
            user_context: Additional user context

        Returns:
            Dictionary with extracted information
        """
        try:
            # Initialize model if needed
            if self._model is None:
                await self._initialize_model()

            # For now, use rule-based extraction (would replace with transformer model)
            extracted_info = self._rule_based_extraction(processed_text, user_context)

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(extracted_info, processed_text)

            extracted_info["confidence_score"] = confidence_score
            extracted_info["model_version"] = "rule-based-v1.0"

            return extracted_info

        except Exception as e:
            raise NLPProcessingError(f"Model inference failed: {str(e)}", error_code="NLP_005")

    async def _initialize_model(self) -> None:
        """Initialize NLP model (placeholder for transformer model)"""
        try:
            # In production, this would load a transformer model
            # For now, we'll use rule-based approach

            # Mock model loading
            self.logger.info(
                "Initializing NLP model (rule-based mode)",
                operation="initialize_model"
            )

            self._model = "rule_based_model"
            self._tokenizer = None

        except Exception as e:
            raise NLPProcessingError(f"Failed to initialize NLP model: {str(e)}", error_code="NLP_006")

    def _rule_based_extraction(self, text: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based information extraction (placeholder for ML model)"""
        extracted_info = {
            "extracted_urls": self._extract_urls_from_text(text),
            "data_descriptions": self._extract_data_descriptions(text),
            "data_types": self._identify_data_type(text),
            "output_requirements": self._extract_output_requirements(text),
            "ambiguity_flags": self._identify_ambiguities(text)
        }

        # Enhance with user context
        if user_context:
            extracted_info.update(self._process_user_context(user_context, extracted_info))

        return extracted_info

    def _extract_urls_from_text(self, text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = r'https?://[^\s\)]+'
        urls = re.findall(url_pattern, text, re.IGNORECASE)

        # Add known government websites based on keywords
        keyword_urls = {
            "金管局": ["https://www.hkma.gov.hk"],
            "hkma": ["https://www.hkma.gov.hk"],
            "統計處": ["https://www.censtatd.gov.hk"],
            "censtatd": ["https://www.censtatd.gov.hk"],
            "差餉": ["https://www.rvd.gov.hk"],
            "rvd": ["https://www.rvd.gov.hk"],
            "政府": ["https://www.info.gov.hk", "https://www.gov.hk"]
        }

        for keyword, urls in keyword_urls.items():
            if keyword in text.lower() and not any(url in text for url in urls):
                urls.extend(urls)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)

        return unique_urls

    def _extract_data_descriptions(self, text: str) -> List[str]:
        """Extract data descriptions from text"""
        # Split text into potential data descriptions
        descriptions = []

        # Look for patterns indicating data types
        data_patterns = [
            r'(hibor|利率).*?數據',
            r'(gdp|國內生產總值).*?數據',
            r'(失業率|就業).*?統計',
            r'(樓價|物業).*?指數',
            r'(cpi|消費物價).*?數據',
            r'(貿易|進出口).*?數據'
        ]

        for pattern in data_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract the full phrase containing the match
                words = text.split()
                for i, word in enumerate(words):
                    if match.lower() in word.lower():
                        # Extract a window around the match
                        start = max(0, i - 2)
                        end = min(len(words), i + 3)
                        phrase = " ".join(words[start:end])
                        if phrase not in descriptions:
                            descriptions.append(phrase)

        # If no specific patterns found, use the full text as description
        if not descriptions:
            descriptions.append(text.strip())

        return descriptions[:3]  # Limit to top 3 descriptions

    def _identify_data_type(self, text: str) -> List[str]:
        """Identify data types from text"""
        data_type_mapping = {
            "interest_rates": ["hibor", "利率", "interest", "rate"],
            "gdp": ["gdp", "國內生產總值", "economic", "output"],
            "unemployment": ["失業", "unemployment", "就業", "employment"],
            "property_prices": ["樓價", "物業", "property", "housing", "real estate"],
            "trade": ["貿易", "trade", "進口", "出口", "import", "export"],
            "inflation": ["cpi", "消費物價", "inflation", "物價指數"]
        }

        identified_types = []
        text_lower = text.lower()

        for data_type, keywords in data_type_mapping.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_types.append(data_type)

        return identified_types or ["general"]

    def _extract_output_requirements(self, text: str) -> Dict[str, Any]:
        """Extract output format and field requirements"""
        requirements = {
            "format": "json",  # Default format
            "fields": self._extract_expected_fields(text)
        }

        # Check for specific format requirements
        if "csv" in text.lower():
            requirements["format"] = "csv"
        elif "xml" in text.lower():
            requirements["format"] = "xml"
        elif "yaml" in text.lower():
            requirements["format"] = "yaml"

        return requirements

    def _extract_expected_fields(self, text: str) -> List[str]:
        """Extract expected data fields from description"""
        field_mapping = {
            "date": ["日期", "date", "時間", "time"],
            "rate": ["利率", "rate", "比率"],
            "overnight": ["隔夜", "overnight"],
            "week": ["週", "week", "一週"],
            "month": ["月", "month", "個月"],
            "quarter": ["季", "quarter", "季度"],
            "year": ["年", "year", "年度"],
            "amount": ["金額", "amount", "總值"],
            "growth": ["增長", "growth", "增長率"],
            "index": ["指數", "index"],
            "price": ["價格", "price", "價"]
        }

        expected_fields = ["date"]  # Always include date
        text_lower = text.lower()

        for field, keywords in field_mapping.items():
            if any(keyword in text_lower for keyword in keywords):
                if field not in expected_fields:
                    expected_fields.append(field)

        # Add specific fields based on data type
        if "hibor" in text_lower or "利率" in text_lower:
            hibor_fields = ["overnight_rate", "one_week_rate", "one_month_rate", "three_month_rate", "six_month_rate"]
            for field in hibor_fields:
                if field not in expected_fields:
                    expected_fields.append(field)

        return expected_fields[:10]  # Limit to reasonable number of fields

    def _identify_ambiguities(self, text: str) -> List[str]:
        """Identify potential ambiguities in the request"""
        ambiguities = []

        # Check for vague descriptions
        vague_phrases = ["一些數據", "某些信息", "抓取數據", "獲取信息"]
        for phrase in vague_phrases:
            if phrase in text:
                ambiguities.append("description_too_vague")
                break

        # Check for missing URLs
        if not self._extract_urls_from_text(text):
            ambiguities.append("missing_target_url")

        # Check for missing data type
        if not self._identify_data_type(text) or self._identify_data_type(text) == ["general"]:
            ambiguities.append("missing_data_type")

        # Check for very short descriptions
        if len(text.strip()) < 20:
            ambiguities.append("description_too_short")

        return ambiguities

    def _process_user_context(self, user_context: Dict[str, Any], extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process and integrate user context with extracted information"""
        context_enhancements = {}

        # Add URLs from context if none found in text
        if "target_website" in user_context and not extracted_info["extracted_urls"]:
            context_enhancements["extracted_urls"] = [user_context["target_website"]]

        # Add data type from context if none identified
        if "data_type" in user_context and (not extracted_info["data_types"] or extracted_info["data_types"] == ["general"]):
            context_enhancements["data_types"] = [user_context["data_type"]]

        # Override output format if specified in context
        if "output_format" in user_context:
            context_enhancements["output_requirements"] = extracted_info["output_requirements"].copy()
            context_enhancements["output_requirements"]["format"] = user_context["output_format"]

        return context_enhancements

    def _calculate_confidence_score(self, extracted_info: Dict[str, Any], original_text: str) -> float:
        """Calculate confidence score for extraction results"""
        confidence = 0.5  # Base confidence

        # Increase confidence based on extracted URLs
        if extracted_info.get("extracted_urls"):
            confidence += 0.2

        # Increase confidence based on identified data types
        if extracted_info.get("data_types") and extracted_info["data_types"] != ["general"]:
            confidence += 0.15

        # Increase confidence based on number of expected fields
        fields = extracted_info.get("output_requirements", {}).get("fields", [])
        if len(fields) > 2:
            confidence += 0.1

        # Decrease confidence based on ambiguities
        ambiguities = extracted_info.get("ambiguity_flags", [])
        confidence -= len(ambiguities) * 0.1

        # Decrease confidence for very short or very long texts
        text_length = len(original_text)
        if text_length < 20:
            confidence -= 0.2
        elif text_length > 500:
            confidence -= 0.1

        # Ensure confidence is within valid range
        confidence = max(0.1, min(0.99, confidence))

        return round(confidence, 2)

    async def _structure_nlp_result(
        self,
        request_id: str,
        nlp_result: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> NLPProcessingResult:
        """Structure NLP result into proper format"""
        return NLPProcessingResult(
            request_id=request_id,
            confidence_score=nlp_result.get("confidence_score", 0.5),
            extracted_urls=nlp_result.get("extracted_urls", []),
            data_descriptions=nlp_result.get("data_descriptions", []),
            output_requirements=nlp_result.get("output_requirements", {}),
            ambiguity_flags=nlp_result.get("ambiguity_flags", []),
            processing_status=ProcessingStatus.COMPLETED,
            user_context=user_context,
            model_version=nlp_result.get("model_version", "unknown")
        )

    async def _validate_processing_result(self, result: NLPProcessingResult) -> None:
        """Validate processing result meets minimum requirements"""
        if result.confidence_score < 0.1:
            raise NLPProcessingError("Extremely low confidence score", error_code="NLP_007")

        if not result.extracted_urls and not result.ambiguity_flags:
            # Only fail if no URLs and no ambiguities detected
            raise NLPProcessingError("No URLs extracted and no ambiguities flagged", error_code="NLP_008")

        # Ensure required fields are present
        if not result.output_requirements:
            result.output_requirements = {"format": "json", "fields": ["date", "value"]}


class NLPProcessor:
    """Enhanced NLP processor with advanced capabilities"""

    def __init__(self):
        self.logger = StructuredLogger("scraping.nlp_processor")
        self.interface = NLPInterface()

    async def process_single_request(self, request: NaturalLanguageRequest) -> NLPProcessingResult:
        """Process a single natural language request"""
        return await self.interface.process_request(request)

    async def batch_process(self, requests: List[NaturalLanguageRequest]) -> List[NLPProcessingResult]:
        """Process multiple requests in batch"""
        results = []

        # Process requests concurrently
        tasks = [self.process_single_request(request) for request in requests]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions in results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result
                    error_result = NLPProcessingResult(
                        request_id=requests[i].request_id,
                        confidence_score=0.0,
                        processing_status=ProcessingStatus.FAILED,
                        ambiguity_flags=["processing_error"]
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)

            return processed_results

        except Exception as e:
            self.logger.error(
                f"Batch processing failed: {str(e)}",
                batch_size=len(requests),
                operation="batch_process"
            )
            raise NLPProcessingError(f"Batch processing failed: {str(e)}", error_code="NLP_009")

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for NLP processing"""
        # Basic preprocessing
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)

        return text

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction (would use more sophisticated NLP in production)
        keywords = []

        # Financial data keywords
        financial_keywords = [
            "hibor", "利率", "gdp", "失業率", "樓價", "cpi", "貿易",
            "overnight", "隔夜", "week", "週", "month", "月", "quarter", "季"
        ]

        for keyword in financial_keywords:
            if keyword.lower() in text.lower():
                keywords.append(keyword)

        return keywords

    def _parse_date_frequency(self, text: str) -> str:
        """Parse date frequency from text"""
        frequency_mapping = {
            "每日": "daily",
            "每天": "daily",
            "週": "weekly",
            "星期": "weekly",
            "月": "monthly",
            "月份": "monthly",
            "季": "quarterly",
            "季度": "quarterly",
            "年": "yearly",
            "年度": "yearly"
        }

        text_lower = text.lower()
        for chinese, english in frequency_mapping.items():
            if chinese in text_lower:
                return english

        return "unknown"


# Convenience functions
def create_nlp_interface(config=None) -> NLPInterface:
    """Create NLP interface instance"""
    return NLPInterface(config)


def create_nlp_processor() -> NLPProcessor:
    """Create NLP processor instance"""
    return NLPProcessor()