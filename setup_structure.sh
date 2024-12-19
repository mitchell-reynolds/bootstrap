#!/usr/bin/env bash

# Build env and MongoDB
conda create --name bootstrap
conda activate bootstrap --file=environments.yml
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

echo "Conda env & MongoDB instance created successfully"

python data_ingest/extract_load_clinical_trials.py
python data_ingest/extract_load_fda_approvals.py
python data_ingest/extract_load_stocks.py

echo "Extracted & loaded up clinical trials, FDA approvals, and relevant stocks"

python data_cleaning/filter_clinical_trials.py
python data_cleaning/filter_fda.py
python data_cleaning/combine_fda_and_ct.py
python data_cleaning/filter_drugs.py

echo "Filtered clinical trials & FDA approvals to only keep successful drugs"

python viz/plot_stock_time_series.py

echo "Check the './viz/figures/' folder for all graphs"

conda deactivate
