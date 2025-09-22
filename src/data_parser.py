"""
Apple Health Data Parser

This module parses Apple Health XML export files and extracts relevant health metrics
including glucose readings, activity data, sleep data, and other physiological measurements.
"""

import xml.etree.ElementTree as ET
import pandas as pd
from typing import List, Optional
import logging


class AppleHealthParser:
    """Parser for Apple Health XML export data."""

    def __init__(self, xml_file_path: str):
        """
        Initialize the parser with the path to the Apple Health XML file.

        Args:
            xml_file_path (str): Path to the Apple Health export.xml file
        """
        self.xml_file_path = xml_file_path
        self.tree = None
        self.root = None

    def load_xml(self) -> bool:
        """
        Load and parse the XML file.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.tree = ET.parse(self.xml_file_path)
            self.root = self.tree.getroot()
            logging.info(f"Successfully loaded XML file: {self.xml_file_path}")
            return True
        except ET.ParseError as e:
            logging.error(f"Error parsing XML file: {e}")
            return False
        except FileNotFoundError:
            logging.error(f"XML file not found: {self.xml_file_path}")
            return False

    def extract_health_records(
        self, record_types: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Extract health records from the XML file.

        Args:
            record_types (List[str], optional): Specific record types to extract.
                                              If None, extracts all records.

        Returns:
            pd.DataFrame: DataFrame containing health records
        """
        if self.root is None:
            raise ValueError("XML file not loaded. Call load_xml() first.")

        records = []

        for record in self.root.findall(".//Record"):
            record_type = record.get("type")

            # Filter by record types if specified
            if record_types and record_type not in record_types:
                continue

            record_data = {
                "type": record_type,
                "sourceName": record.get("sourceName"),
                "value": record.get("value"),
                "unit": record.get("unit"),
                "creationDate": record.get("creationDate"),
                "startDate": record.get("startDate"),
                "endDate": record.get("endDate"),
            }
            records.append(record_data)

        df = pd.DataFrame(records)

        # Convert date columns to datetime
        date_columns = ["creationDate", "startDate", "endDate"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Convert value column to numeric where possible
        if "value" in df.columns:
            df["value"] = pd.to_numeric(df["value"], errors="coerce")

        return df

    def extract_workouts(self) -> pd.DataFrame:
        """
        Extract workout data from the XML file.

        Returns:
            pd.DataFrame: DataFrame containing workout records
        """
        if self.root is None:
            raise ValueError("XML file not loaded. Call load_xml() first.")

        workouts = []

        for workout in self.root.findall(".//Workout"):
            workout_data = {
                "workoutActivityType": workout.get("workoutActivityType"),
                "duration": workout.get("duration"),
                "durationUnit": workout.get("durationUnit"),
                "totalDistance": workout.get("totalDistance"),
                "totalDistanceUnit": workout.get("totalDistanceUnit"),
                "totalEnergyBurned": workout.get("totalEnergyBurned"),
                "totalEnergyBurnedUnit": workout.get("totalEnergyBurnedUnit"),
                "sourceName": workout.get("sourceName"),
                "creationDate": workout.get("creationDate"),
                "startDate": workout.get("startDate"),
                "endDate": workout.get("endDate"),
            }
            workouts.append(workout_data)

        df = pd.DataFrame(workouts)

        # Convert date columns to datetime
        date_columns = ["creationDate", "startDate", "endDate"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Convert numeric columns
        numeric_columns = ["duration", "totalDistance", "totalEnergyBurned"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def get_glucose_data(self) -> pd.DataFrame:
        """
        Extract glucose-related data from Apple Health.

        Returns:
            pd.DataFrame: DataFrame containing glucose measurements
        """
        glucose_types = [
            "HKQuantityTypeIdentifierBloodGlucose",
            "HKCategoryTypeIdentifierInsulinDelivery",
        ]

        glucose_df = self.extract_health_records(glucose_types)
        return glucose_df

    def get_activity_data(self) -> pd.DataFrame:
        """
        Extract activity-related data from Apple Health.

        Returns:
            pd.DataFrame: DataFrame containing activity measurements
        """
        activity_types = [
            "HKQuantityTypeIdentifierStepCount",
            "HKQuantityTypeIdentifierDistanceWalkingRunning",
            "HKQuantityTypeIdentifierActiveEnergyBurned",
            "HKQuantityTypeIdentifierBasalEnergyBurned",
            "HKQuantityTypeIdentifierFlightsClimbed",
        ]

        activity_df = self.extract_health_records(activity_types)
        return activity_df

    def get_sleep_data(self) -> pd.DataFrame:
        """
        Extract sleep-related data from Apple Health.

        Returns:
            pd.DataFrame: DataFrame containing sleep measurements
        """
        sleep_types = ["HKCategoryTypeIdentifierSleepAnalysis"]

        sleep_df = self.extract_health_records(sleep_types)
        return sleep_df


if __name__ == "__main__":
    # Example usage
    parser = AppleHealthParser("../data/raw/export.xml")
    if parser.load_xml():
        glucose_data = parser.get_glucose_data()
        activity_data = parser.get_activity_data()
        print(f"Extracted {len(glucose_data)} glucose records")
        print(f"Extracted {len(activity_data)} activity records")
