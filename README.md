# Bootstrap Bio - Take Home Analysis

[See Google Doc here](https://docs.google.com/document/d/1gTC7-phKevo7qJZr3LecRARh2zT2D-3F2IWBKjhZJOQ/edit?tab=t.0)

## Notes to future self
- Use [the ClinicalTrail.gov API](https://clinicaltrials.gov/data-api/about-api) and not their [search feature](https://clinicaltrials.gov/search?resFirstPost=2014-11-21_2024-11-21&aggFilters=results:with) (purposefully using the KISS method as the data is small enough as `HasResults` field is only ~50k). Check out [PyTrials](https://github.com/jvfe/pytrials/tree/master) first before writing one's own connector
- Once I had the data, there were a lot of non stock companies and I chose to pick the largest organizations (eg GlaxoSmithKline, Pfizer etc.) of the 7k+ institutions.
- [Study showing this works](https://pmc.ncbi.nlm.nih.gov/articles/PMC9439234/); [another paper](https://www.nature.com/articles/s41598-023-39301-4)
- Need to add collaborators `study['protocolSection']['sponsorCollaboratorsModule'].get('collaborators', {}).get('name', 'Unknown')`
- Seems like the results need to be tied to a paper's abstract to determine success or failure of the intervention?