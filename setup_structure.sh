#!/usr/bin/env bash

# Build env and MongoDB
conda create --name bootstrap
conda activate bootstrap --file=environments.yml
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
python data_ingest/download_clinical_trials.py
# TODO
conda deactivate

echo "Conda env & MongoDB created successfully"