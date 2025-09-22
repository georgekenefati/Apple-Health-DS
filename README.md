# Apple Health & Freestyle Libre 3 Data Analysis

## Overview
This project performs Exploratory Data Analysis (EDA) on personal Apple Health data and Freestyle Libre 3 glucose monitoring data, merging them by datetime to discover insights about health patterns and glucose trends.

## 🎯 Project Goals
- **SQL Skills**: Demonstrate data management, joins, and aggregations
- **Data Science**: Use pandas for analysis and machine learning for modeling
- **Personal Data**: Analyze real physiological data for meaningful insights
- **Professional Presentation**: Create a portfolio-ready analysis

## 📁 Project Structure
```
├── data/                   # Raw and processed data files
│   ├── raw/               # Original Apple Health XML and Libre CSV
│   ├── processed/         # Cleaned and merged datasets
│   └── database/          # SQLite database files
├── notebooks/             # Jupyter notebooks for analysis
│   ├── 01_data_extraction.ipynb
│   ├── 02_data_cleaning.ipynb  
│   ├── 03_exploratory_analysis.ipynb
│   └── 04_modeling.ipynb
├── src/                   # Python modules
│   ├── data_parser.py     # Apple Health XML parser
│   ├── glucose_processor.py # Libre data processor
│   ├── data_merger.py     # Datetime-based data merger
│   └── visualizations.py # Plotting functions
├── sql/                   # SQL queries and schema
│   ├── schema.sql        # Database schema
│   ├── data_quality.sql  # Data validation queries
│   └── analysis_queries.sql # Analytical queries
└── outputs/              # Generated plots and reports
    ├── figures/          # Visualization outputs
    └── reports/          # Analysis summaries
```

## 🔧 Setup Instructions

### Prerequisites
- Python 3.8+
- Jupyter Notebook
- SQLite3

### Installation
1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Data Sources
1. **Apple Health Data**: Export your health data from iPhone Health app
   - Open Health app → Profile → Export All Health Data
   - Place `export.xml` in `data/raw/`

2. **Freestyle Libre 3 Data**: Export glucose data from LibreView
   - Login to LibreView → Reports → Export Data
   - Place CSV file in `data/raw/`

## 📊 Analysis Workflow

### 1. Data Extraction (`notebooks/01_data_extraction.ipynb`)
- Parse Apple Health XML export
- Process Freestyle Libre CSV data
- Initial data exploration and validation

### 2. Data Cleaning (`notebooks/02_data_cleaning.ipynb`)
- Handle missing values and outliers
- Standardize datetime formats
- Data quality assessment

### 3. SQL Data Management (`sql/`)
- Create SQLite database schema
- Load cleaned data into database
- Perform joins and aggregations

### 4. Exploratory Analysis (`notebooks/03_exploratory_analysis.ipynb`)
- Temporal patterns in health metrics
- Glucose variability analysis
- Correlation with activity and sleep data

### 5. Machine Learning (`notebooks/04_modeling.ipynb`)
- Glucose prediction models
- Pattern recognition in health data
- Feature importance analysis

## 🔍 Key Insights Expected
- Glucose patterns related to meals, exercise, and sleep
- Health metric correlations and trends
- Personalized health recommendations based on data

## 🛠 Technologies Used
- **Python**: pandas, numpy, scikit-learn
- **SQL**: SQLite for data management
- **Visualization**: matplotlib, seaborn, plotly
- **ML**: Regression and time series analysis

## 📈 Results
Analysis results and visualizations will be stored in the `outputs/` directory, providing insights into personal health patterns and glucose management.

---
*This project demonstrates professional data science skills using real-world health data for meaningful personal insights.*
