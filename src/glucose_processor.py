"""
Freestyle Libre 3 Glucose Data Processor

This module processes CSV exports from Freestyle Libre 3 glucose monitoring system
and prepares the data for analysis and merging with Apple Health data.
"""

import pandas as pd
from typing import Dict
import logging


class LibreGlucoseProcessor:
    """Processor for Freestyle Libre 3 glucose data."""

    def __init__(self, csv_file_path: str):
        """
        Initialize the processor with the path to the Libre CSV file.

        Args:
            csv_file_path (str): Path to the Freestyle Libre CSV export
        """
        self.csv_file_path = csv_file_path
        self.raw_data = None
        self.processed_data = None

    def load_csv(self) -> bool:
        """
        Load the CSV file and perform initial processing.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Libre CSV files may have different formats, try common encodings
            encodings = ["utf-8", "iso-8859-1", "cp1252"]

            for encoding in encodings:
                try:
                    self.raw_data = pd.read_csv(
                        self.csv_file_path, encoding=encoding, skiprows=1
                    )
                    logging.info(f"Successfully loaded CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue

            if self.raw_data is None:
                raise ValueError(
                    "Could not decode CSV file with any supported encoding"
                )

            logging.info(
                f"Loaded {len(self.raw_data)} glucose records from {self.csv_file_path}"
            )
            return True

        except FileNotFoundError:
            logging.error(f"CSV file not found: {self.csv_file_path}")
            return False
        except Exception as e:
            logging.error(f"Error loading CSV file: {e}")
            return False

    def standardize_columns(self) -> None:
        """
        Standardize column names to a consistent format.
        Libre exports may have different column names depending on region/version.
        """
        if self.raw_data is None:
            raise ValueError("CSV file not loaded. Call load_csv() first.")

        # Common column name mappings for Libre data
        column_mappings = {
            # Timestamp columns
            "Device Timestamp": "timestamp",
            "Timestamp (YYYY-MM-DD HH:MM:SS)": "timestamp",
            "Time": "timestamp",
            "Date": "date",
            # Glucose value columns
            "Historic Glucose mg/dL": "glucose_mg_dl",
            "Historic Glucose (mg/dL)": "glucose_mg_dl",
            "Historic Glucose mmol/L": "glucose_mmol_l",
            "Glucose Value (mg/dL)": "glucose_mg_dl",
            "Glucose Value (mmol/L)": "glucose_mmol_l",
            "Record Type": "record_type",
            # Scan glucose (real-time readings)
            "Scan Glucose mg/dL": "scan_glucose_mg_dl",
            "Scan Glucose (mg/dL)": "scan_glucose_mg_dl",
            "Scan Glucose mmol/L": "scan_glucose_mmol_l",
            # Strip glucose (fingerstick readings)
            "Strip Glucose mg/dL": "strip_glucose_mg_dl",
            "Strip Glucose (mg/dL)": "strip_glucose_mg_dl",
            "Strip Glucose mmol/L": "strip_glucose_mmol_l",
            # Additional fields
            "Notes": "notes",
            "Serial Number": "serial_number",
            "Device": "device",
            "Ketone mmol/L": "ketone_mmol_l",
            "Rapid-Acting Insulin (units)": "rapid_acting_insulin_units",
            "Carbohydrates (grams)": "carbohydrates_grams",
            "Long-Acting Insulin (units)": "long_acting_insulin_units",
        }

        # Apply mappings
        self.raw_data.rename(columns=column_mappings, inplace=True)

        # Ensure we have required columns
        required_columns = ["timestamp", "glucose_mg_dl"]
        missing_columns = [
            col for col in required_columns if col not in self.raw_data.columns
        ]

        if missing_columns:
            logging.warning(f"Missing required columns: {missing_columns}")

    def clean_and_process(self) -> pd.DataFrame:
        """
        Clean and process the glucose data.

        Returns:
            pd.DataFrame: Cleaned and processed glucose data
        """
        if self.raw_data is None:
            raise ValueError("CSV file not loaded. Call load_csv() first.")

        self.standardize_columns()

        df = self.raw_data.copy()

        # Convert timestamp to datetime
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # Handle glucose values - convert to mg/dL if in mmol/L
        if "glucose_mmol_l" in df.columns and "glucose_mg_dl" not in df.columns:
            df["glucose_mg_dl"] = df["glucose_mmol_l"] * 18.0182  # Conversion factor

        # Combine different glucose reading types
        glucose_columns = ["glucose_mg_dl", "scan_glucose_mg_dl", "strip_glucose_mg_dl"]
        df["glucose_value"] = df[glucose_columns].bfill(axis=1).iloc[:, 0]

        # Add glucose source information
        df["glucose_source"] = "historic"
        if "scan_glucose_mg_dl" in df.columns:
            df.loc[df["scan_glucose_mg_dl"].notna(), "glucose_source"] = "scan"
        if "strip_glucose_mg_dl" in df.columns:
            df.loc[df["strip_glucose_mg_dl"].notna(), "glucose_source"] = "fingerstick"

        # Remove invalid readings
        df = df[df["glucose_value"].between(20, 600)]  # Reasonable glucose range

        # Remove duplicate timestamps
        df = df.drop_duplicates(subset=["timestamp"])

        # Sort by timestamp
        df = df.sort_values("timestamp")

        # Add derived features
        df = self._add_glucose_metrics(df)

        self.processed_data = df

        logging.info(f"Processed {len(df)} valid glucose records")
        return df

    def _add_glucose_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived glucose metrics to the dataframe.

        Args:
            df (pd.DataFrame): DataFrame with glucose data

        Returns:
            pd.DataFrame: DataFrame with additional metrics
        """
        # Calculate glucose rate of change
        df["glucose_rate_change"] = (
            df["glucose_value"].diff() / df["timestamp"].diff().dt.total_seconds() * 60
        )

        # Add glucose trend categories
        df["glucose_trend"] = "stable"
        df.loc[df["glucose_rate_change"] > 2, "glucose_trend"] = "rising_fast"
        df.loc[df["glucose_rate_change"].between(1, 2), "glucose_trend"] = "rising"
        df.loc[df["glucose_rate_change"].between(-1, -2), "glucose_trend"] = "falling"
        df.loc[df["glucose_rate_change"] < -2, "glucose_trend"] = "falling_fast"

        # Add time-based features
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["is_weekend"] = df["day_of_week"].isin([5, 6])

        # Add glucose range categories
        df["glucose_range"] = "normal"
        df.loc[df["glucose_value"] < 70, "glucose_range"] = "low"
        df.loc[df["glucose_value"] > 180, "glucose_range"] = "high"
        df.loc[df["glucose_value"] < 54, "glucose_range"] = "very_low"
        df.loc[df["glucose_value"] > 250, "glucose_range"] = "very_high"

        return df

    def get_time_in_range_stats(self) -> Dict[str, float]:
        """
        Calculate time-in-range statistics for glucose data.

        Returns:
            Dict[str, float]: Dictionary containing TIR statistics
        """
        if self.processed_data is None:
            raise ValueError("Data not processed. Call clean_and_process() first.")

        df = self.processed_data
        total_readings = len(df)

        if total_readings == 0:
            return {}

        stats = {
            "time_very_low_percent": (df["glucose_range"] == "very_low").sum()
            / total_readings
            * 100,
            "time_low_percent": (df["glucose_range"] == "low").sum()
            / total_readings
            * 100,
            "time_in_range_percent": (df["glucose_range"] == "normal").sum()
            / total_readings
            * 100,
            "time_high_percent": (df["glucose_range"] == "high").sum()
            / total_readings
            * 100,
            "time_very_high_percent": (df["glucose_range"] == "very_high").sum()
            / total_readings
            * 100,
            "average_glucose": df["glucose_value"].mean(),
            "glucose_std": df["glucose_value"].std(),
            "coefficient_variation": (
                df["glucose_value"].std() / df["glucose_value"].mean()
            )
            * 100,
        }

        return stats

    def resample_data(self, frequency: str = "15T") -> pd.DataFrame:
        """
        Resample glucose data to a specified frequency.

        Args:
            frequency (str): Pandas frequency string (e.g., '15T' for 15 minutes)

        Returns:
            pd.DataFrame: Resampled glucose data
        """
        if self.processed_data is None:
            raise ValueError("Data not processed. Call clean_and_process() first.")

        df = self.processed_data.copy()
        df.set_index("timestamp", inplace=True)

        # Resample numeric columns
        numeric_columns = ["glucose_value", "glucose_rate_change"]
        resampled = df[numeric_columns].resample(frequency).mean()

        # Forward fill missing values (within reason)
        resampled = resampled.fillna(method="ffill", limit=2)

        resampled.reset_index(inplace=True)

        return resampled


if __name__ == "__main__":
    # Example usage
    processor = LibreGlucoseProcessor("../data/raw/libre_export.csv")
    if processor.load_csv():
        processed_data = processor.clean_and_process()
        stats = processor.get_time_in_range_stats()
        print(f"Processed {len(processed_data)} glucose readings")
        print(f"Time in range: {stats.get('time_in_range_percent', 0):.1f}%")
