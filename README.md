# ReadNext

**"If you liked this, read that."** A recommendation engine for manga and light novels.

Pick a category, browse the catalog, open a title and get recommendations based on what makes that title special: its genres, themes and tags.

> **Status:** Early development. See the [roadmap](#roadmap) below.

---

## The problem

Finding your next manga or light novel is hard. Most sites recommend whatever is popular. NextVolume recommends titles that are actually *similar* to the one you liked, and explains why:

> *Recommended because it shares: isekai, adventure, slow pacing etc.*

## How it works

```
AniList API ──► Python ingestion ──► Snowflake (RAW)
                                        │
                                        ▼
                                 dbt: staging → marts
                                        │
                                        ▼
                         Precomputed recommendations
                                        │
                                        ▼
                                  Streamlit app
```

1. **Ingestion:** Python pulls manga and light novel data from the AniList GraphQL API, incrementally and idempotently.
2. **Storage:** Raw JSON lands in Snowflake.
3. **Transformation:** dbt models clean the data into a dimensional model (titles, genres, tags).
4. **Recommendations:** Similarity scores are precomputed in the pipeline, so the app only reads finished results.
5. **App:** A Streamlit site where you browse the catalog and see recommendations for each title.

## Tech stack

| Layer | Tool |
|---|---|
| Source | AniList GraphQL API |
| Ingestion | Python |
| Warehouse | Snowflake |
| Transformation | dbt |
| App | Streamlit |
| CI/CD | GitHub Actions |

## Project structure

```
nextvolume/
├── ingestion/   # Python scripts that fetch data from AniList
├── dbt/         # dbt project: staging and mart models, tests
├── app/         # Streamlit app
└── docs/        # Architecture diagrams and design notes
```

## Roadmap

### Phase 1: Foundation
- Ingest manga and light novels from AniList into Snowflake
- dbt models for titles, genres and tags
- Data quality tests in dbt

### Phase 2: First recommendations
- Tag-based similarity between titles
- Streamlit app: pick a category, browse the catalog, open a title and see recommendations
- Scheduled pipeline runs

### Phase 3: Smarter recommendations
- Embeddings and "mood search" on free text
- Evaluation of recommendation quality

### Phase 4: Beyond manga
- Bridge to regular novels ("liked this manga? try this novel")

## Design decisions

*Documented as the project grows.*

## Data source

Data provided by [AniList](https://anilist.co) via their public API. This is a non-commercial portfolio project.