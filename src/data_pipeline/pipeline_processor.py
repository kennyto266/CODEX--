"""
Pipeline Processor Module - Alternative Data Pipeline

Orchestrates the complete data processing pipeline.

Pipeline Flow:
    Raw Data
        ↓
    [DataCleaner]      → Handle missing values, outliers
        ↓
    [TemporalAligner]   → Align to trading days, generate features
        ↓
    [DataNormalizer]    → Normalize for ML models
        ↓
    [QualityScorer]     → Assess final quality
        ↓
    Processed Data (Ready for ML/Analysis)

Features:
    - Configurable pipeline steps
    - Progress tracking for large datasets
    - Error recovery and logging
    - Checkpoint/resume capability
    - Performance metrics

Usage:
    processor = PipelineProcessor()
    processor.add_step("clean", "DataCleaner", config={...})
    processor.add_step("align", "TemporalAligner", config={...})
    processor.add_step("normalize", "DataNormalizer", config={...})
    processor.add_step("score", "QualityScorer", config={...})

    result = processor.process(df)
    print(processor.get_report())
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

import pandas as pd
import numpy as np

from .data_cleaner import DataCleaner
from .temporal_aligner import TemporalAligner
from .data_normalizer import DataNormalizer
from .quality_scorer import QualityScorer

logger = logging.getLogger("hk_quant_system.pipeline_processor")


class PipelineStep(Enum):
    """Available pipeline steps"""
    CLEAN = "clean"
    ALIGN = "align"
    NORMALIZE = "normalize"
    SCORE = "score"
    CUSTOM = "custom"


class PipelineProcessor:
    """
    Pipeline processor for alternative data.

    Orchestrates sequential data processing steps:
    1. Cleaning (missing values, outliers)
    2. Alignment (temporal, frequency)
    3. Normalization (standardization)
    4. Quality Scoring (validation)

    Supports custom steps and error recovery.
    """

    def __init__(
        self,
        checkpoint_enabled: bool = True,
        verbose: bool = True,
    ):
        """
        Initialize PipelineProcessor.

        Args:
            checkpoint_enabled: Enable checkpoint/resume
            verbose: Enable verbose logging
        """
        self.steps: List[Dict[str, Any]] = []
        self.checkpoint_enabled = checkpoint_enabled
        self.verbose = verbose

        # Execution tracking
        self.execution_log = {
            "start_time": None,
            "end_time": None,
            "duration_seconds": None,
            "steps_executed": [],
            "errors": [],
            "checkpoints": [],
        }

        # Statistics
        self.statistics = {
            "initial_rows": 0,
            "final_rows": 0,
            "initial_columns": 0,
            "final_columns": 0,
            "quality_score": None,
        }

        logger.info("Initialized PipelineProcessor")

    def add_step(
        self,
        name: str,
        step_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> "PipelineProcessor":
        """
        Add a processing step to the pipeline.

        Args:
            name: Step name (for logging)
            step_type: Type of step ("clean", "align", "normalize", "score", "custom")
            config: Configuration for this step

        Returns:
            Self for chaining
        """
        if config is None:
            config = {}

        step_info = {
            "name": name,
            "type": step_type,
            "config": config,
            "status": "pending",
        }

        self.steps.append(step_info)
        logger.info(f"Added step '{name}' (type: {step_type})")

        return self

    def process(
        self,
        df: pd.DataFrame,
        date_column: Optional[str] = None,
        numeric_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Execute the complete pipeline.

        Args:
            df: Input DataFrame
            date_column: Name of date column (for temporal alignment)
            numeric_columns: Numeric columns to process

        Returns:
            Processed DataFrame
        """
        if df.empty:
            logger.error("Empty DataFrame provided")
            return df

        # Initialize tracking
        start_time = datetime.now()
        self.execution_log["start_time"] = start_time.isoformat()
        self.statistics["initial_rows"] = len(df)
        self.statistics["initial_columns"] = len(df.columns)

        if self.verbose:
            logger.info(
                f"Starting pipeline processing: "
                f"{len(df)} rows, {len(df.columns)} columns"
            )

        result = df.copy()

        # Identify numeric columns if not specified
        if numeric_columns is None:
            numeric_columns = result.select_dtypes(include=[np.number]).columns.tolist()

        # Execute each step
        for i, step in enumerate(self.steps):
            try:
                if self.verbose:
                    logger.info(f"[{i+1}/{len(self.steps)}] Executing: {step['name']}")

                result = self._execute_step(
                    result,
                    step,
                    date_column,
                    numeric_columns,
                )

                step["status"] = "completed"
                self.execution_log["steps_executed"].append(step["name"])

                if self.checkpoint_enabled:
                    self.execution_log["checkpoints"].append({
                        "step": step["name"],
                        "timestamp": datetime.now().isoformat(),
                        "rows": len(result),
                    })

            except Exception as e:
                error_msg = f"Step '{step['name']}' failed: {str(e)}"
                logger.error(error_msg)
                self.execution_log["errors"].append(error_msg)
                step["status"] = "failed"

                # Continue to next step or stop?
                if self.verbose:
                    logger.warning(f"Error in step {step['name']}, continuing...")

        # Final statistics
        end_time = datetime.now()
        self.execution_log["end_time"] = end_time.isoformat()
        self.execution_log["duration_seconds"] = (
            end_time - start_time
        ).total_seconds()

        self.statistics["final_rows"] = len(result)
        self.statistics["final_columns"] = len(result.columns)

        if self.verbose:
            logger.info(
                f"Pipeline completed in {self.execution_log['duration_seconds']:.2f}s: "
                f"{len(df)} → {len(result)} rows, "
                f"{len(df.columns)} → {len(result.columns)} columns"
            )

        return result

    def _execute_step(
        self,
        df: pd.DataFrame,
        step: Dict[str, Any],
        date_column: Optional[str],
        numeric_columns: List[str],
    ) -> pd.DataFrame:
        """Execute a single pipeline step."""
        step_type = step["type"]
        config = step["config"]

        if step_type == "clean":
            cleaner = DataCleaner(
                missing_value_strategy=config.get(
                    "missing_value_strategy", "interpolate"
                ),
                outlier_strategy=config.get("outlier_strategy", "cap"),
                z_score_threshold=config.get("z_score_threshold", 3.0),
                iqr_multiplier=config.get("iqr_multiplier", 1.5),
            )
            result = cleaner.clean(df, numeric_columns, date_column)

        elif step_type == "align":
            aligner = TemporalAligner()

            # Align to trading days
            if config.get("align_to_trading_days", True):
                result = aligner.align_to_trading_days(
                    df,
                    date_column or "date",
                    fill_method=config.get("fill_method", "forward_fill"),
                )
            else:
                result = df.copy()

            # Generate lagged features
            if config.get("generate_lags", False):
                result = aligner.generate_lagged_features(
                    result,
                    columns=config.get("lag_columns"),
                    lags=config.get("lags", [1, 5, 20]),
                )

            # Generate rolling features
            if config.get("generate_rolling", False):
                result = aligner.generate_rolling_features(
                    result,
                    columns=config.get("rolling_columns"),
                    windows=config.get("windows", [5, 20, 60]),
                    functions=config.get("functions", ["mean", "std"]),
                )

            # Compute returns
            if config.get("compute_returns", False):
                result = aligner.compute_returns(
                    result,
                    price_columns=config.get("price_columns"),
                    return_type=config.get("return_type", "log"),
                    periods=config.get("return_periods", [1, 5, 20]),
                )

        elif step_type == "normalize":
            normalizer = DataNormalizer(
                method=config.get("method", "zscore"),
                eps=config.get("eps", 1e-8),
            )
            result = normalizer.fit_transform(
                df,
                columns=config.get("columns", numeric_columns),
            )

        elif step_type == "score":
            scorer = QualityScorer(
                completeness_weight=config.get("completeness_weight", 0.5),
                freshness_weight=config.get("freshness_weight", 0.3),
                consistency_weight=config.get("consistency_weight", 0.2),
                max_age_hours=config.get("max_age_hours", 24),
            )
            score = scorer.calculate_quality(df, date_column, numeric_columns)
            self.statistics["quality_score"] = score

            result = df.copy()

        else:
            logger.warning(f"Unknown step type: {step_type}")
            result = df.copy()

        return result

    def get_report(self) -> Dict[str, Any]:
        """Get execution report."""
        return {
            "execution": self.execution_log,
            "statistics": self.statistics,
            "steps": [
                {
                    "name": s["name"],
                    "type": s["type"],
                    "status": s["status"],
                }
                for s in self.steps
            ],
        }

    def print_report(self) -> None:
        """Print human-readable execution report."""
        report = self.get_report()

        lines = [
            "=" * 70,
            "PIPELINE EXECUTION REPORT",
            "=" * 70,
            "",
            "EXECUTION SUMMARY",
            "-" * 70,
            f"Start Time: {self.execution_log['start_time']}",
            f"End Time: {self.execution_log['end_time']}",
            f"Duration: {self.execution_log['duration_seconds']:.2f} seconds",
            f"Steps Executed: {len(self.execution_log['steps_executed'])}/{len(self.steps)}",
            "",
            "DATA STATISTICS",
            "-" * 70,
            f"Initial: {self.statistics['initial_rows']} rows, "
            f"{self.statistics['initial_columns']} columns",
            f"Final: {self.statistics['final_rows']} rows, "
            f"{self.statistics['final_columns']} columns",
            f"Quality Score: {self.statistics['quality_score']:.1%}"
            if self.statistics["quality_score"] is not None else "N/A",
            "",
            "STEPS EXECUTED",
            "-" * 70,
        ]

        for i, step_name in enumerate(self.execution_log["steps_executed"], 1):
            lines.append(f"  {i}. {step_name} ✓")

        if self.execution_log["errors"]:
            lines.extend([
                "",
                "ERRORS",
                "-" * 70,
            ])
            for error in self.execution_log["errors"]:
                lines.append(f"  ✗ {error}")

        lines.append("=" * 70)

        print("\n".join(lines))

    def get_step_status(self, step_name: str) -> Optional[str]:
        """Get status of a specific step."""
        for step in self.steps:
            if step["name"] == step_name:
                return step["status"]
        return None

    def has_errors(self) -> bool:
        """Check if pipeline had errors."""
        return len(self.execution_log["errors"]) > 0


# Usage examples
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range("2025-09-01", "2025-10-31", freq="D")
    dates_trading = [d for d in dates if d.weekday() < 5]

    data = {
        "date": dates_trading[:30],
        "volume": np.random.randint(1000, 10000, 30),
        "price": np.random.uniform(50, 150, 30),
    }
    df = pd.DataFrame(data)

    # Introduce some issues
    df.loc[5, "volume"] = np.nan
    df.loc[10, "price"] = 500  # Outlier

    print("Original DataFrame:")
    print(df.head(10))
    print(f"\nShape: {df.shape}")

    # Create pipeline
    processor = PipelineProcessor(verbose=True)

    # Add steps
    processor.add_step(
        "clean",
        "clean",
        config={
            "missing_value_strategy": "interpolate",
            "outlier_strategy": "cap",
        },
    )

    processor.add_step(
        "align",
        "align",
        config={
            "align_to_trading_days": True,
            "generate_lags": True,
            "lag_columns": ["volume", "price"],
            "lags": [1, 5],
        },
    )

    processor.add_step(
        "normalize",
        "normalize",
        config={
            "method": "zscore",
            "columns": ["volume", "price"],
        },
    )

    processor.add_step(
        "score",
        "score",
        config={
            "completeness_weight": 0.5,
        },
    )

    # Process
    result = processor.process(df, date_column="date")

    print("\nProcessed DataFrame:")
    print(result.head(10))
    print(f"\nShape: {result.shape}")

    # Print report
    processor.print_report()
