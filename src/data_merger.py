"""
Data Merger Module

This module merges Apple Health data with Freestyle Libre glucose data
based on datetime alignment, creating a unified dataset for analysis.
"""

import pandas as pd
from typing import Dict
import logging


class HealthDataMerger:
    """Merges Apple Health and Freestyle Libre glucose data."""

    def __init__(self):
        """Initialize the data merger."""
        self.apple_health_data = None
        self.glucose_data = None
        self.merged_data = None

    def load_apple_health_data(self, data: pd.DataFrame) -> None:
        """
        Load Apple Health data for merging.

        Args:
            data (pd.DataFrame): Processed Apple Health data
        """
        self.apple_health_data = data.copy()
        logging.info(f"Loaded {len(data)} Apple Health records")

    def load_glucose_data(self, data: pd.DataFrame) -> None:
        """
        Load glucose data for merging.

        Args:
            data (pd.DataFrame): Processed glucose data
        """
        self.glucose_data = data.copy()
        logging.info(f"Loaded {len(data)} glucose records")

    def align_timestamps(self, tolerance_minutes: int = 15) -> pd.DataFrame:
        """
        Merge datasets using timestamp alignment with tolerance.

        Args:
            tolerance_minutes (int): Maximum time difference for matching records

        Returns:
            pd.DataFrame: Merged dataset
        """
        if self.apple_health_data is None or self.glucose_data is None:
            raise ValueError("Both datasets must be loaded before merging")

        # Prepare glucose data
        glucose_df = self.glucose_data.copy()
        glucose_df = glucose_df.rename(columns={"timestamp": "glucose_timestamp"})

        # Prepare Apple Health data - use startDate as primary timestamp
        health_df = self.apple_health_data.copy()
        if "startDate" in health_df.columns:
            health_df = health_df.rename(columns={"startDate": "health_timestamp"})
        else:
            raise ValueError("Apple Health data must have startDate column")

        # Create time-based merge using pd.merge_asof
        # Sort both dataframes by timestamp
        glucose_df = glucose_df.sort_values("glucose_timestamp")
        health_df = health_df.sort_values("health_timestamp")

        # Use merge_asof for nearest timestamp matching
        tolerance = pd.Timedelta(minutes=tolerance_minutes)

        merged_df = pd.merge_asof(
            health_df,
            glucose_df,
            left_on="health_timestamp",
            right_on="glucose_timestamp",
            tolerance=tolerance,
            direction="nearest",
        )

        # Remove records where no glucose match was found
        merged_df = merged_df.dropna(subset=["glucose_timestamp"])

        # Calculate time difference between matched records
        merged_df["time_diff_minutes"] = (
            merged_df["health_timestamp"] - merged_df["glucose_timestamp"]
        ).dt.total_seconds() / 60

        self.merged_data = merged_df

        logging.info(f"Merged data contains {len(merged_df)} aligned records")
        return merged_df

    def create_time_windows(self, window_minutes: int = 60) -> pd.DataFrame:
        """
        Create time windows and aggregate data within each window.

        Args:
            window_minutes (int): Size of time windows in minutes

        Returns:
            pd.DataFrame: Windowed and aggregated data
        """
        if self.merged_data is None:
            raise ValueError("Data must be merged before creating time windows")

        df = self.merged_data.copy()

        # Use glucose timestamp as the primary time reference
        df.set_index("glucose_timestamp", inplace=True)

        # Create time windows
        window_freq = f"{window_minutes}T"

        # Aggregate numeric columns
        numeric_cols = df.select_dtypes(include=["number"]).columns
        windowed_data = (
            df[numeric_cols]
            .resample(window_freq)
            .agg(
                {
                    "glucose_value": ["mean", "std", "count"],
                    "value": ["mean", "sum"],  # Apple Health value
                    "time_diff_minutes": "mean",
                }
            )
        )

        # Flatten column names
        windowed_data.columns = ["_".join(col).strip() for col in windowed_data.columns]

        # Add categorical data (most frequent value in window)
        categorical_cols = ["type", "glucose_range", "glucose_trend", "sourceName"]
        for col in categorical_cols:
            if col in df.columns:
                windowed_data[f"{col}_mode"] = (
                    df[col]
                    .resample(window_freq)
                    .agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None)
                )

        # Remove windows with no glucose data
        windowed_data = windowed_data.dropna(subset=["glucose_value_mean"])

        windowed_data.reset_index(inplace=True)

        logging.info(f"Created {len(windowed_data)} time windows")
        return windowed_data

    def add_contextual_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add contextual features based on timing and patterns.

        Args:
            df (pd.DataFrame): DataFrame to add features to

        Returns:
            pd.DataFrame: DataFrame with additional features
        """
        df = df.copy()

        # Time-based features
        if "glucose_timestamp" in df.columns:
            timestamp_col = "glucose_timestamp"
        elif "health_timestamp" in df.columns:
            timestamp_col = "health_timestamp"
        else:
            logging.warning("No timestamp column found for feature engineering")
            return df

        df["hour"] = df[timestamp_col].dt.hour
        df["day_of_week"] = df[timestamp_col].dt.dayofweek
        df["is_weekend"] = df["day_of_week"].isin([5, 6])
        df["is_night"] = df["hour"].between(22, 6)
        df["is_morning"] = df["hour"].between(6, 12)
        df["is_afternoon"] = df["hour"].between(12, 18)
        df["is_evening"] = df["hour"].between(18, 22)

        # Meal timing approximation
        df["likely_meal_time"] = (
            df["hour"].between(7, 9)  # Breakfast
            | df["hour"].between(12, 14)  # Lunch
            | df["hour"].between(18, 20)  # Dinner
        )

        return df

    def get_correlation_analysis(self) -> Dict[str, float]:
        """
        Calculate correlations between glucose values and health metrics.

        Returns:
            Dict[str, float]: Correlation coefficients
        """
        if self.merged_data is None:
            raise ValueError("Data must be merged before correlation analysis")

        df = self.merged_data.copy()

        # Select numeric columns for correlation
        numeric_cols = df.select_dtypes(include=["number"]).columns

        correlations = {}

        if "glucose_value" in df.columns:
            for col in numeric_cols:
                if col != "glucose_value" and df[col].notna().sum() > 10:
                    corr = df["glucose_value"].corr(df[col])
                    if not pd.isna(corr):
                        correlations[col] = corr

        # Sort by absolute correlation strength
        correlations = dict(
            sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
        )

        return correlations

    def export_merged_data(self, file_path: str, format_type: str = "csv") -> None:
        """
        Export merged data to file.

        Args:
            file_path (str): Path to save the file
            format_type (str): Format type ('csv', 'parquet', 'json')
        """
        if self.merged_data is None:
            raise ValueError("No merged data to export")

        if format_type.lower() == "csv":
            self.merged_data.to_csv(file_path, index=False)
        elif format_type.lower() == "parquet":
            self.merged_data.to_parquet(file_path, index=False)
        elif format_type.lower() == "json":
            self.merged_data.to_json(file_path, orient="records", date_format="iso")
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        logging.info(f"Exported merged data to {file_path}")


if __name__ == "__main__":
    # Example usage
    merger = HealthDataMerger()

    # This would typically be called with actual data
    # merger.load_apple_health_data(apple_health_df)
    # merger.load_glucose_data(glucose_df)
    # merged_data = merger.align_timestamps(tolerance_minutes=15)
    # correlations = merger.get_correlation_analysis()

    print("Data merger module ready for use")
