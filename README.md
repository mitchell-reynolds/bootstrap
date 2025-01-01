# Bootstrap Bio - Take Home Analysis

Key Question: If we knew the results of some percentage of clinical trials, what sort of ROI should we expect? How much does each stock move for each announcement? 
Get BioPharmCatalyst and add it to the invoice

[See Google Doc here](https://docs.google.com/document/d/1gTC7-phKevo7qJZr3LecRARh2zT2D-3F2IWBKjhZJOQ/edit?tab=t.0)

# QUICKSTART (CLI)
With [Anaconda](https://docs.anaconda.com/anaconda/install/)
and [MongoDB](https://www.mongodb.com/docs/manual/installation/)
installed, run this commands to get up and running in ~10min 
as you'll download the entire clinicaltrials.gov database and FDA approval file.

_Note, I have a Macbook with the M2 chip so your environment might not translate._
_The better path would be to have this spun up in a server but that's a later problem_ 😉

```
chmod +x setup_structure.sh
./setup_structure.sh
```

# Notes to future self
- FDA data only shows True Positives (ie it does _not_ return drugs failing approval eg Simufilam by NASDAQ:SAVA)
   - Relatedly, there might be issues on comparing 
- Using [the ClinicalTrail.gov API](https://clinicaltrials.gov/data-api/about-api) and not their [search feature](https://clinicaltrials.gov/search?resFirstPost=2014-11-21_2024-11-21&aggFilters=results:with)
- Once I had all the Lead Sponsors from Clinical Trials, I manually downloaded and joined NYSE and NASDAQ data to get ~300 companies of the 7k.
- [Study showing this works](https://pmc.ncbi.nlm.nih.gov/articles/PMC9439234/) that used a data service that's prohibitively expensive; [another paper](https://www.nature.com/articles/s41598-023-39301-4) that used [BioPharmaAnalyst data](https://www.biopharmcatalyst.com/sign-up)
- Make modular updates to MongoDB vs slash & burn
- Use OpenFDA API instead of the [manual download](https://open.fda.gov/apis/drug/drugsfda/download/) that was uploaded & updated on Dec 12, 2024
- There are often multiple names associated with a drug across data sources 
   - eg In the FDA, BIZENGRI is the brand name for the active ingredient "ZENOCUTUZUMAB-ZBCO" but Clinical Trials has "Zenocutuzumab" and "MCLA-128"
   - The sponsor matches (FDA `MERUS N.V.`; CT `Merus N.V.`)
- Maybe use [Regulations.gov API](https://open.gsa.gov/api/regulationsgov/) to pull data on comments made about companies?

# Data Dictionary

## Clinical Trials
```
protocolSection.identificationModule.nctId (always one value)
protocolSection.sponsorCollaboratorsModule.leadSponsor.name (always one value)
protocolSection.statusModule.lastUpdatePostDateStruct.date (always one value)
protocolSection.interventions.name (but not `name: 'Placebo'`; this can still return multiple values)
protocolSection.interventions.otherNames (list)
protocolSection.statusModule.overallStatus (directional but not definitive)
protocolSection.oversightModule.isFdaRegulatedDrug
protocolSection.designModule.phases ('PHASE3')
protocolSection.statusModule.lastUpdateSubmitDate
```

## FDA
```
results.application_number (unique ID)
results.sponsor_name (might match `company_ct`)
products.brand_name
products.active_ingredients
openfda.substance_name
openfda.generic_name
results.submissions.submission_status_date (when submission_type = "ORIG" and submission_code = "AP")
results.submissions.submission_status, 
results.submissions.submission_class_code
```

# Project Structure```
project_root/
├─ data_ingest/
│  ├─ extract_load_clinical_trials.py
│  ├─ extract_load_fda_approvals.py
│  ├─ extract_load_stocks.py
│  └─ raw_data/
│
├─ data_cleaning/
│  ├─ combine_fda_and_ct.py
│  ├─ filter_clinical_trials.py
│  ├─ filter_fda_approvals.py
│  ├─ filter_stocks.py
│  ├─ integrate_stocks_and_drugs.py
│  └─ processed_data/
│
├─ viz/
│  ├─ plot_stock_time_series.py
│  └─ figures/ (PNG, HTML)
│
├─ models/
│  ├─ feature_engineering.py
│  ├─ train_model.py
│  ├─ evaluate_model.py
│  └─ saved_models/
│
├─ utils/
│  ├─ config.py
│  ├─ helpers.py
│  └─ constants.py
│
└─ README.md
```