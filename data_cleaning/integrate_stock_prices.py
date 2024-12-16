import pandas as pd
import pymongo

MONGO_URI = "mongodb://localhost:27017/"  # Default MongoDB location on local
db_name = "clinical_trials_db"
collection_name = "studies"

print("Setting up MongoDB")
client = pymongo.MongoClient(MONGO_URI)
db = client[db_name]
collection = db[collection_name]

sponsor_pipeline = [
  {
    "$match": {
      "protocolSection.sponsorCollaboratorsModule.leadSponsor.class": "INDUSTRY"
    }
  },
  {
    "$group": {
      "_id": "$protocolSection.sponsorCollaboratorsModule.leadSponsor.name",
      "sponsor_num_trials": { "$sum": 1 }
    }
  },
  {
    "$sort": {
      "sponsor_num_trials": -1
    }
  },
  {
    "$project": {
      "company_ct": "$_id",
      "sponsor_num_trials": 1,
      "_id": 0
    }
  }
]

collab_pipeline = [
  {
    "$unwind": "$protocolSection.sponsorCollaboratorsModule.collaborators"
  },
  {
    "$match": {
      "protocolSection.sponsorCollaboratorsModule.collaborators.class": "INDUSTRY"
    }
  },
  {
    "$group": {
      "_id": "$protocolSection.sponsorCollaboratorsModule.collaborators.name",
      "collab_num_trials": { "$sum": 1 }
    }
  },
  {
    "$sort": {
      "collab_num_trials": -1
    }
  },
  {
    "$project": {
      "company_ct": "$_id",
      "collab_num_trials": 1,
      "_id": 0
    }
  }
]

print("Running pipelines")
collab_result = list(collection.aggregate(collab_pipeline))
sponsor_result = list(collection.aggregate(sponsor_pipeline))

df_sponsor = pd.DataFrame(sponsor_result)
df_collab = pd.DataFrame(collab_result)

# Write DataFrames to CSV
output_dir = "./data_cleaning/processed_data/"
df_sponsor.to_csv(f"{output_dir}sponsor_data.csv", index=False)
df_collab.to_csv(f"{output_dir}collaborator_data.csv", index=False)

# Join on public_company_potential
merged_df = pd.merge(df_sponsor, df_collab, on="company_ct", how="outer").fillna(0)
merged_df["total_num_trials"] = merged_df["sponsor_num_trials"] + merged_df["collab_num_trials"]
merged_df.to_csv(f"{output_dir}merged_data.csv", index=False)
