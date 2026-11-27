# ReadNext

**"If you liked this, read that."** A recommendation engine for manga and light novels.

Pick a title you liked and get recommendations based on what makes it special: its themes, mood and tags. Every recommendation comes with an explanation of why.

**Live demo:** https://readnext-fgzbsijsxfhgnxwappuzcl.streamlit.app/

> **Status:** The full pipeline and the app are live. Next up: smarter weighting of tags. See the [roadmap](#roadmap).

---

## The problem

*Manga* are Japanese comics and *light novels* are short Japanese novels, often with illustrations. Both have huge catalogs, and finding your next one is hard. Most sites recommend whatever is popular. ReadNext recommends titles that are actually *similar* to the one you liked, and explains why.

## What the output looks like

Every title gets a list of the 10 most similar titles. Each recommendation has a **similarity score** from 0 to 1 and the **tags the two titles share**, so the app can say why it was recommended:

| Title | Recommended | Score | Why |
|---|---|---|---|
| A quiet fantasy story about travel and loss | A slow-paced story about two girls travelling through a ruined world | 0.42 | Travel, Philosophy, Calm mood |

You don't need to know anything about manga to use it: the tags describe themes and mood in plain words, and the score shows how strong the match is.

## How it works

```
AniList API ──► Python ──► Snowflake RAW ──► dbt STAGING ──► dbt MARTS ──► Parquet ──► Streamlit app
                (ingest)   (raw JSON)        (clean views)   (tables +       (export)    (live demo)
                                                              recommendations)
```

1. **Ingestion** (`ingestion/anilist_to_raw.py`): Python fetches manga and light novels from the AniList GraphQL API, 50 titles per request, and loads them into Snowflake as raw JSON.
2. **Staging** (`dbt/models/staging`): dbt turns the raw JSON into typed, clearly named columns.
3. **Marts** (`dbt/models/marts`): dbt builds the tables the app reads from:
   - `dim_title`: the catalog, one row per title
   - `bridge_title_genre` and `bridge_title_tag`: genres and tags, one row per title and genre/tag
   - `fct_recommendations`: the 10 most similar titles for every title
4. **Export** (`ingestion/export_marts.py`): the finished tables are saved as small Parquet files in `app/data/`.
5. **App** (`app/streamlit_app.py`): a Streamlit site where you pick manga or light novels, search and filter the catalog, open a title and see its recommendations with the reasons behind them.

### How the recommendations are calculated

`fct_recommendations` is plain SQL in dbt:

1. Every tag gets a weight from 0 to 1 based on how well it fits the title (AniList's tag rank). Weak tags (rank below 50) are left out.
2. Two titles get points for every tag they share: `weight_a × weight_b`.
3. The points are normalised by each title's total tag weight (**cosine similarity**), so titles don't win just because they have many tags. The score ends up between 0 and 1.
4. The 10 best matches per title are kept, together with the 3 shared tags that contributed most. Those tags become the explanation in the app.

## Tech stack

| Layer | Tool |
|---|---|
| Source | AniList GraphQL API |
| Ingestion | Python (`requests`, `snowflake-connector-python`) |
| Warehouse | Snowflake |
| Transformation and tests | dbt |
| App | Streamlit, hosted on Streamlit Community Cloud |

## Project structure

```
readnext/
├── snowflake/              # One-time setup SQL (warehouse, database, schemas, role, service user)
├── ingestion/              # Python: AniList → Snowflake RAW, and export to Parquet
├── dbt/
│   ├── models/staging/     # Raw JSON → clean columns (views)
│   ├── models/marts/       # Catalog, genres, tags and recommendations (tables)
│   ├── tests/              # Custom SQL tests
│   └── macros/             # Custom schema naming
└── app/
    ├── streamlit_app.py    # The app
    └── data/               # Parquet snapshot the app reads
```

## Run it yourself

<details>
<summary>Setup steps</summary>

1. **Python environment** (Python 3.13; dbt does not support 3.15 yet)
   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Key pair** for the Snowflake service user
   ```bash
   mkdir keys
   openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out keys/rsa_key.p8 -nocrypt
   openssl rsa -in keys/rsa_key.p8 -pubout -out keys/rsa_key.pub
   ```
3. **Snowflake setup:** paste the public key into `snowflake/setup.sql` and run it in Snowsight as `ACCOUNTADMIN`.
4. **Settings:** copy `.env.example` to `.env` and fill in your account identifier.
5. **Load data and build models**
   ```bash
   set -a; source .env; set +a
   python ingestion/anilist_to_raw.py
   dbt build --project-dir dbt --profiles-dir dbt
   ```
6. **Export and run the app**
   ```bash
   python ingestion/export_marts.py
   streamlit run app/streamlit_app.py
   ```
</details>

## Roadmap

### Phase 1: Foundation
- Ingest manga and light novels from AniList into Snowflake
- dbt models for titles, genres and tags
- Data quality tests in dbt

### Phase 2: First recommendations
- Tag-based similarity between titles
- Streamlit app: pick a category, browse the catalog, open a title and see recommendations
- Live demo on Streamlit Community Cloud
- Down-weight common tags (IDF) so broad tags like "Magic" count less than rare, more specific ones
- Scheduled pipeline runs

### Phase 3: Smarter recommendations
- Embeddings and "mood search" on free text
- Evaluation of recommendation quality

### Phase 4: Beyond manga
- Bridge to regular novels ("liked this manga? try this novel")

## Design decisions

- **Raw data is stored untouched as JSON.** The full API response lands in a `VARIANT` column. All cleaning happens in dbt, so the models can be rebuilt or changed at any time without calling the API again.
- **Idempotent loading.** Each page is loaded with a `MERGE` on the AniList id. Running the ingestion twice updates titles instead of creating duplicates.
- **Respecting the API's limits.** The script pauses between requests and waits for the time AniList asks for (`Retry-After`) if it gets a `429`. AniList also only returns the first 5 000 results of a query, so manga and light novels are fetched in separate queries (up to 5 000 of each).
- **The app reads a Parquet snapshot.** The finished marts tables are exported to small Parquet files committed to the repo. The live demo runs without a warehouse connection, so it keeps working and costs nothing to host.
- **Views in staging, tables in marts.** Staging views are cheap and always up to date. Marts are tables because the app reads them often and they should be fast.
- **Recommendations are precomputed.** Similarity is calculated in the pipeline, not when a user clicks. The app only reads finished results, which keeps it fast and simple.
- **Tests on data and relationships.** dbt tests check unique and non-null ids, allowed values, that every row in the bridge and recommendation tables points to a real title, and that no title is recommended to itself.
- **Key pair authentication with a dedicated service user.** Pipelines connect as `READNEXT_SVC` (`TYPE = SERVICE`) using an RSA key pair instead of a password. Snowflake is phasing out single-factor passwords, and a service user with its own least-privilege role (`READNEXT_ROLE`) is how automated pipelines are set up in production.
- **Cost control.** An `XSMALL` warehouse that auto-suspends after 60 seconds.

## Known limitations

- **Broad tags carry too much weight.** Tags like "Magic" appear on hundreds of titles and say little about what makes a story special. Because of that, a calm, reflective story can get a loud action series as a recommendation, just because both involve magic. Next step: IDF weighting, which gives rare tags more weight than common ones (the same idea search engines use).
- **Same story in different formats.** Many stories exist both as a manga (comic) and a light novel (book). The two versions have almost identical tags, so they often end up as each other's top recommendation. Filtering on AniList's data about related titles would fix this.
- **Snapshot data.** The app shows the data from the latest export. New titles and score changes on AniList show up after the pipeline is run again.
- **Most popular titles only.** The catalog covers the most popular manga and light novels on AniList (up to 5 000 of each), not every title ever published.

## Data source

Data provided by [AniList](https://anilist.co) via their public API. This is a non-commercial portfolio project.


