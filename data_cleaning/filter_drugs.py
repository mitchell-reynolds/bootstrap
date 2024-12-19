import pandas as pd

df = pd.read_csv('./data_cleaning/processed_data/combine_fda_and_ct.csv')

# Convert 'ct_date' and 'fda_date' to datetime
df['ct_date'] = pd.to_datetime(df['ct_date'], format='%Y-%m-%d', errors='coerce').combine_first(pd.to_datetime(df['ct_date'], format='%Y-%m', errors='coerce'))
df['fda_date'] = pd.to_datetime(df['fda_date'], format='%Y%m%d', errors='coerce')

# Filter for drugs that have been approved by FDA after the start of the clinical trial and remove any mention of phase 1
df = df[(df['fda_date'] >= df['ct_date']) | (df['fda_date'].isna())]
df = df[~df['ct_phase'].str.contains('PHASE1', na=False)]

# Sort by company name then by fda_date both ascending
df = df.sort_values(by=['fda_company', 'fda_date'], ascending=[True, True])

df.to_csv('./data_cleaning/processed_data/filtered_drugs.csv', index=False)
