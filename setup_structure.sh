#!/usr/bin/env bash

# Create directory structure
mkdir -p data_ingest/raw_data
mkdir -p data_cleaning/processed_data
mkdir -p models/saved_models
mkdir -p visualization/figures
mkdir -p utils

# Create placeholder Python files for data ingestion
touch data_ingest/download_clinical_trials.py
touch data_ingest/fetch_fda_approvals.py
touch data_ingest/fetch_stock_data.py

# Create placeholder Python files for data cleaning
touch data_cleaning/clean_clinical_trials.py
touch data_cleaning/merge_with_fda_data.py
touch data_cleaning/integrate_stock_prices.py

# Create placeholder Python files for modeling
touch models/feature_engineering.py
touch models/train_model.py
touch models/evaluate_model.py

# Create a placeholder Python file for visualization
touch visualization/plot_stock_time_series.py

# Create placeholder Python files for utils
touch utils/config.py
touch utils/helpers.py
touch utils/constants.py

# Create top-level files
touch requirements.txt
touch README.md

echo "Project structure created successfully."