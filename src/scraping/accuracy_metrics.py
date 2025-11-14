"""
Accuracy metrics and validation for NLP processing

Provides comprehensive accuracy evaluation metrics for natural language processing
results including URL extraction, data type identification, field extraction,
and confidence calibration.
"""

import json
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import statistics

from .models import NLPProcessingResult
from .logging_config import StructuredLogger


@dataclass
class AccuracyResult:
    """Result of accuracy evaluation"""
    metric_name: str
    accuracy_score: float
    true_positives: int
    false_positives: int
    false_negatives: int
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of benchmark evaluation"""
    case_id: str
    description: str
    overall_accuracy: float
    component_accuracies: Dict[str, float]
    confidence_score: float
    processing_time: float
    meets_threshold: bool
    errors: List[str] = field(default_factory=list)


class AccuracyMetrics:
    """Calculator for various NLP accuracy metrics"""

    def __init__(self):
        self.logger = StructuredLogger("scraping.accuracy_metrics")

    def evaluate_url_extraction(
        self,
        predicted_urls: List[str],
        expected_urls: List[str],
        allow_partial_match: bool = True
    ) -> bool:
        """
        Evaluate URL extraction accuracy

        Args:
            predicted_urls: URLs extracted by NLP
            expected_urls: Ground truth URLs
            allow_partial_match: Allow partial domain matches

        Returns:
            True if extraction is accurate
        """
        if not predicted_urls and not expected_urls:
            return True  # Both empty is correct

        if not predicted_urls or not expected_urls:
            return False  # One empty, one not is incorrect

        if allow_partial_match:
            # Check for domain matches
            predicted_domains = {self._extract_domain(url) for url in predicted_urls}
            expected_domains = {self._extract_domain(url) for url in expected_urls}

            intersection = predicted_domains.intersection(expected_domains)
            return len(intersection) > 0
        else:
            # Exact match required
            predicted_set = set(predicted_urls)
            expected_set = set(expected_urls)

            intersection = predicted_set.intersection(expected_set)
            return len(intersection) >= min(len(predicted_set), len(expected_set))

    def evaluate_data_type_identification(
        self,
        predicted_type: str,
        expected_type: str,
        allow_synonyms: bool = True
    ) -> bool:
        """
        Evaluate data type identification accuracy

        Args:
            predicted_type: Data type identified by NLP
            expected_type: Ground truth data type
            allow_synonyms: Allow synonymous data types

        Returns:
            True if identification is accurate
        """
        if predicted_type == expected_type:
            return True

        if allow_synonyms:
            synonyms = {
                "interest_rates": ["hibor", "interest", "rates"],
                "gdp": ["gdp", "economic_output", "domestic_product"],
                "unemployment": ["unemployment", "jobless", "employment"],
                "property_prices": ["property", "real_estate", "housing"],
                "trade": ["trade", "imports", "exports"],
                "inflation": ["inflation", "cpi", "consumer_prices"]
            }

            # Check if types are in the same synonym group
            for type_group, type_synonyms in synonyms.items():
                if (predicted_type in type_synonyms and expected_type in type_synonyms) or \
                   (predicted_type == type_group and expected_type in type_synonyms) or \
                   (expected_type == type_group and predicted_type in type_synonyms):
                    return True

        return False

    def evaluate_field_extraction(
        self,
        predicted_fields: List[str],
        expected_fields: List[str],
        similarity_threshold: float = 0.8
    ) -> float:
        """
        Evaluate field extraction accuracy

        Args:
            predicted_fields: Fields extracted by NLP
            expected_fields: Ground truth fields
            similarity_threshold: Minimum similarity score for partial matches

        Returns:
            Accuracy score between 0.0 and 1.0
        """
        if not predicted_fields and not expected_fields:
            return 1.0

        if not predicted_fields or not expected_fields:
            return 0.0

        # Calculate exact matches
        exact_matches = len(set(predicted_fields).intersection(set(expected_fields)))

        # Calculate semantic matches for remaining fields
        semantic_matches = 0
        for pred_field in predicted_fields:
            if pred_field not in expected_fields:
                for exp_field in expected_fields:
                    if self._calculate_field_similarity(pred_field, exp_field) >= similarity_threshold:
                        semantic_matches += 1
                        break

        total_matches = exact_matches + semantic_matches
        max_matches = max(len(predicted_fields), len(expected_fields))

        return total_matches / max_matches

    def evaluate_format_detection(
        self,
        predicted_format: str,
        expected_format: str
    ) -> bool:
        """
        Evaluate output format detection accuracy

        Args:
            predicted_format: Format detected by NLP
            expected_format: Ground truth format

        Returns:
            True if format detection is accurate
        """
        return predicted_format.lower() == expected_format.lower()

    def calculate_confidence_calibration(
        self,
        results: List[Tuple[float, float]]
    ) -> Dict[str, float]:
        """
        Calculate confidence calibration metrics

        Args:
            results: List of (confidence_score, actual_accuracy) tuples

        Returns:
            Dictionary with calibration metrics
        """
        if not results:
            return {"correlation": 0.0, "mean_error": 0.0, "rms_error": 0.0}

        confidence_scores = [conf for conf, _ in results]
        actual_accuracies = [acc for _, acc in results]

        # Calculate correlation
        if len(confidence_scores) > 1:
            correlation = self._calculate_correlation(confidence_scores, actual_accuracies)
        else:
            correlation = 0.0

        # Calculate errors
        errors = [abs(conf - acc) for conf, acc in results]
        mean_error = statistics.mean(errors)
        rms_error = statistics.sqrt(statistics.mean(e * e for e in errors))

        return {
            "correlation": correlation,
            "mean_error": mean_error,
            "rms_error": rms_error,
            "sample_size": len(results)
        }

    def generate_accuracy_report(
        self,
        evaluation_results: List[AccuracyResult]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive accuracy report

        Args:
            evaluation_results: List of accuracy evaluation results

        Returns:
            Comprehensive accuracy report
        """
        if not evaluation_results:
            return {"error": "No evaluation results provided"}

        # Calculate overall metrics
        total_accuracy = statistics.mean(result.accuracy_score for result in evaluation_results)
        accuracy_variance = statistics.variance(result.accuracy_score for result in evaluation_results) if len(evaluation_results) > 1 else 0.0

        # Group by metric type
        metric_groups = {}
        for result in evaluation_results:
            metric_type = result.metric_name.split("_")[0]  # e.g., "url" from "url_extraction"
            if metric_type not in metric_groups:
                metric_groups[metric_type] = []
            metric_groups[metric_type].append(result.accuracy_score)

        # Calculate per-metric statistics
        metric_statistics = {}
        for metric_type, scores in metric_groups.items():
            metric_statistics[metric_type] = {
                "mean": statistics.mean(scores),
                "std": statistics.stdev(scores) if len(scores) > 1 else 0.0,
                "min": min(scores),
                "max": max(scores),
                "count": len(scores)
            }

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_metrics": {
                "mean_accuracy": total_accuracy,
                "accuracy_variance": accuracy_variance,
                "total_evaluations": len(evaluation_results)
            },
            "metric_breakdown": metric_statistics,
            "detailed_results": [
                {
                    "metric": result.metric_name,
                    "accuracy": result.accuracy_score,
                    "true_positives": result.true_positives,
                    "false_positives": result.false_positives,
                    "false_negatives": result.false_negatives,
                    "details": result.details
                }
                for result in evaluation_results
            ]
        }

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return url.lower()

    def _calculate_field_similarity(self, field1: str, field2: str) -> float:
        """Calculate semantic similarity between field names"""
        # Simple similarity based on common tokens
        tokens1 = set(field1.lower().replace('_', ' ').split())
        tokens2 = set(field2.lower().replace('_', ' ').split())

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)

        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5

        if denominator == 0:
            return 0.0

        numerator = n * sum_xy - sum_x * sum_y
        return numerator / denominator


class BenchmarkSuite:
    """Comprehensive benchmark suite for NLP accuracy testing"""

    def __init__(self, data_file: Optional[str] = None):
        self.logger = StructuredLogger("scraping.benchmark_suite")
        self.accuracy_metrics = AccuracyMetrics()
        self.data_file = data_file or "benchmark_data.json"
        self.benchmark_data = []

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Load benchmark dataset"""
        try:
            if Path(self.data_file).exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.benchmark_data = json.load(f)
            else:
                # Use default benchmark data
                self.benchmark_data = self._get_default_benchmark_data()

            self.logger.info(
                f"Loaded {len(self.benchmark_data)} benchmark cases",
                data_file=self.data_file,
                operation="load_dataset"
            )

            return self.benchmark_data

        except Exception as e:
            self.logger.error(
                f"Failed to load benchmark dataset: {str(e)}",
                data_file=self.data_file,
                operation="load_dataset"
            )
            return []

    async def evaluate_single_case(
        self,
        predicted_result: NLPProcessingResult,
        expected_case: Dict[str, Any]
    ) -> float:
        """
        Evaluate single benchmark case

        Args:
            predicted_result: NLP processing result
            expected_case: Expected benchmark case

        Returns:
            Overall accuracy score for this case
        """
        component_scores = {}

        # Evaluate URL extraction
        url_accuracy = self.accuracy_metrics.evaluate_url_extraction(
            predicted_result.extracted_urls,
            expected_case.get("expected_urls", [])
        )
        component_scores["url_extraction"] = float(url_accuracy)

        # Evaluate data type identification
        data_type_accuracy = self.accuracy_metrics.evaluate_data_type_identification(
            self._extract_data_type_from_result(predicted_result),
            expected_case.get("expected_data_type", "")
        )
        component_scores["data_type_identification"] = float(data_type_accuracy)

        # Evaluate field extraction
        expected_fields = expected_case.get("expected_fields", [])
        predicted_fields = predicted_result.output_requirements.get("fields", [])

        field_accuracy = self.accuracy_metrics.evaluate_field_extraction(
            predicted_fields,
            expected_fields
        )
        component_scores["field_extraction"] = field_accuracy

        # Evaluate format detection
        format_accuracy = self.accuracy_metrics.evaluate_format_detection(
            predicted_result.output_requirements.get("format", "json"),
            expected_case.get("expected_format", "json")
        )
        component_scores["format_detection"] = float(format_accuracy)

        # Calculate overall accuracy (weighted average)
        weights = {
            "url_extraction": 0.25,
            "data_type_identification": 0.25,
            "field_extraction": 0.35,
            "format_detection": 0.15
        }

        overall_accuracy = sum(
            component_scores[component] * weights[component]
            for component in component_scores
        )

        self.logger.debug(
            f"Evaluated benchmark case {expected_case.get('id', 'unknown')}",
            case_id=expected_case.get("id"),
            overall_accuracy=overall_accuracy,
            component_scores=component_scores,
            operation="evaluate_single_case"
        )

        return overall_accuracy

    async def run_benchmark(self) -> Dict[str, Any]:
        """
        Run complete benchmark suite

        Returns:
            Comprehensive benchmark results
        """
        start_time = datetime.now()

        dataset = self.load_dataset()
        if not dataset:
            return {"error": "No benchmark data available"}

        case_results = []
        confidence_accuracy_pairs = []

        for case in dataset:
            # This would integrate with actual NLP processing
            # For now, we'll simulate the process
            mock_result = self._simulate_nlp_processing(case)

            # Evaluate the case
            accuracy = await self.evaluate_single_case(mock_result, case)

            # Store result
            case_result = BenchmarkResult(
                case_id=case["id"],
                description=case["description"],
                overall_accuracy=accuracy,
                component_accuracies={},  # Would be populated in real evaluation
                confidence_score=mock_result.confidence_score,
                processing_time=mock_result.processing_time,
                meets_threshold=accuracy >= case.get("confidence_threshold", 0.8)
            )

            case_results.append(case_result)
            confidence_accuracy_pairs.append((mock_result.confidence_score, accuracy))

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # Calculate overall metrics
        overall_metrics = self.calculate_metrics(case_results)

        # Calculate confidence calibration
        calibration_metrics = self.accuracy_metrics.calculate_confidence_calibration(
            confidence_accuracy_pairs
        )

        results = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "total_cases": len(dataset),
            "overall_metrics": overall_metrics,
            "confidence_calibration": calibration_metrics,
            "case_results": [
                {
                    "case_id": result.case_id,
                    "accuracy": result.overall_accuracy,
                    "confidence": result.confidence_score,
                    "meets_threshold": result.meets_threshold
                }
                for result in case_results
            ]
        }

        self.logger.info(
            f"Benchmark completed",
            total_cases=len(dataset),
            overall_accuracy=overall_metrics.get("overall_accuracy", 0.0),
            execution_time=execution_time,
            operation="run_benchmark"
        )

        return results

    def calculate_metrics(self, results: List[BenchmarkResult]) -> Dict[str, float]:
        """Calculate overall benchmark metrics"""
        if not results:
            return {}

        accuracies = [result.overall_accuracy for result in results]
        confidences = [result.confidence_score for result in results]
        processing_times = [result.processing_time for result in results]

        return {
            "overall_accuracy": statistics.mean(accuracies),
            "accuracy_variance": statistics.variance(accuracies) if len(accuracies) > 1 else 0.0,
            "average_confidence": statistics.mean(confidences),
            "confidence_variance": statistics.variance(confidences) if len(confidences) > 1 else 0.0,
            "average_processing_time": statistics.mean(processing_times),
            "cases_meeting_threshold": sum(1 for r in results if r.meets_threshold),
            "threshold_meeting_rate": sum(1 for r in results if r.meets_threshold) / len(results),
            "min_accuracy": min(accuracies),
            "max_accuracy": max(accuracies),
            "median_accuracy": statistics.median(accuracies)
        }

    def save_results(self, results: Dict[str, Any], output_file: str = None) -> str:
        """Save benchmark results to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"benchmark_results_{timestamp}.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            self.logger.info(
                f"Benchmark results saved to {output_file}",
                output_file=output_file,
                operation="save_results"
            )

            return output_file

        except Exception as e:
            self.logger.error(
                f"Failed to save benchmark results: {str(e)}",
                output_file=output_file,
                operation="save_results"
            )
            raise

    def _extract_data_type_from_result(self, result: NLPProcessingResult) -> str:
        """Extract data type from NLP result"""
        # This would be more sophisticated in real implementation
        descriptions = " ".join(result.data_descriptions).lower()

        type_keywords = {
            "interest_rates": ["hibor", "interest", "rate"],
            "gdp": ["gdp", "economic", "output"],
            "unemployment": ["unemployment", "employment"],
            "property_prices": ["property", "housing", "real estate"],
            "trade": ["trade", "import", "export"],
            "inflation": ["inflation", "cpi", "price"]
        }

        for data_type, keywords in type_keywords.items():
            if any(keyword in descriptions for keyword in keywords):
                return data_type

        return "general"

    def _simulate_nlp_processing(self, case: Dict[str, Any]) -> NLPProcessingResult:
        """Simulate NLP processing for testing"""
        import uuid

        # This would be actual NLP processing in real implementation
        return NLPProcessingResult(
            request_id=str(uuid.uuid4()),
            confidence_score=0.85 + (hash(case["id"]) % 15) / 100.0,  # 0.85-0.99 range
            extracted_urls=case.get("expected_urls", []).copy(),
            data_descriptions=[case["description"]],
            output_requirements={
                "format": case.get("expected_format", "json"),
                "fields": case.get("expected_fields", []).copy()
            },
            processing_time=1.0 + (hash(case["id"]) % 30) / 10.0,  # 1.0-4.0 seconds
            model_version="test-model-v1"
        )

    def _get_default_benchmark_data(self) -> List[Dict[str, Any]]:
        """Get default benchmark dataset"""
        return [
            {
                "id": "hibor_001",
                "description": "從香港金管局網站抓取HIBOR利率數據，包括隔夜、1週、1個月、3個月和6個月的歷史利率",
                "expected_urls": ["https://www.hkma.gov.hk"],
                "expected_data_type": "interest_rates",
                "expected_fields": ["date", "overnight_rate", "one_week_rate", "one_month_rate", "three_month_rate", "six_month_rate"],
                "expected_format": "json",
                "confidence_threshold": 0.90
            },
            {
                "id": "gdp_001",
                "description": "從政府統計處獲取香港GDP季度數據，包括國內生產總值和年增長率",
                "expected_urls": ["https://www.censtatd.gov.hk"],
                "expected_data_type": "gdp",
                "expected_fields": ["quarter", "gdp_amount", "growth_rate"],
                "expected_format": "json",
                "confidence_threshold": 0.85
            },
            {
                "id": "property_001",
                "description": "抓取差餉物業估價署的樓價指數數據，包括不同類型物業的價格指數",
                "expected_urls": ["https://www.rvd.gov.hk"],
                "expected_data_type": "property_prices",
                "expected_fields": ["month", "property_type", "price_index"],
                "expected_format": "json",
                "confidence_threshold": 0.85
            }
        ]


# Convenience functions for direct usage
def create_accuracy_metrics() -> AccuracyMetrics:
    """Create AccuracyMetrics instance"""
    return AccuracyMetrics()


def create_benchmark_suite(data_file: str = None) -> BenchmarkSuite:
    """Create BenchmarkSuite instance"""
    return BenchmarkSuite(data_file)