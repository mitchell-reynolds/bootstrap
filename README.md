# Bootstrap Bio - Take Home Analysis

[See Google Doc here](https://docs.google.com/document/d/1gTC7-phKevo7qJZr3LecRARh2zT2D-3F2IWBKjhZJOQ/edit?tab=t.0)

## QUICKSTART (CLI)
With [Anaconda](https://docs.anaconda.com/anaconda/install/)
and [MongoDB](https://www.mongodb.com/docs/manual/installation/)
installed on your local, run this commands to get up and running in ~10min 
as you'll download the entire clinicaltrials.gov database.

_Note, I have a Macbook with the M2 chip so your environment might not translate._
_The better path would be to have this spun up in a server but that's a later problem_ 😉

```
chmod +x setup_structure.sh
```

## Notes to future self
- Using [the ClinicalTrail.gov API](https://clinicaltrials.gov/data-api/about-api) and not their [search feature](https://clinicaltrials.gov/search?resFirstPost=2014-11-21_2024-11-21&aggFilters=results:with)
- Once I had the data, there were a lot of non stock companies and I chose to pick the largest organizations (eg GlaxoSmithKline, Pfizer etc.) of the 7k+ institutions.
- [Study showing this works](https://pmc.ncbi.nlm.nih.gov/articles/PMC9439234/); [another paper](https://www.nature.com/articles/s41598-023-39301-4)
- Need to add collaborators `study['protocolSection']['sponsorCollaboratorsModule'].get('collaborators', {}).get('name', 'Unknown')`
- Seems like the results need to be tied to a paper's abstract to determine success or failure of the intervention?
- Make modular updates to MongoDB vs slash & burn

# Project Structure
```
project_root/
├─ data_ingest/
│  ├─ download_clinical_trials.py
│  ├─ fetch_fda_approvals.py
│  ├─ fetch_stock_data.py
│  └─ raw_data/
│
├─ data_cleaning/
│  ├─ clean_clinical_trials.py
│  ├─ merge_with_fda_data.py
│  ├─ integrate_stock_prices.py
│  └─ processed_data/
│
├─ models/
│  ├─ feature_engineering.py
│  ├─ train_model.py
│  ├─ evaluate_model.py
│  └─ saved_models/
│
├─ visualization/
│  ├─ plot_stock_time_series.py
│  └─ figures/ (PNG, HTML)
│
├─ utils/
│  ├─ config.py
│  ├─ helpers.py
│  └─ constants.py
│
└─ README.md
```