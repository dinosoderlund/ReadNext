"""Export the finished marts tables from Snowflake to Parquet files for the app.

Run from the project root, after `dbt build`:
    python ingestion/export_marts.py

The app reads these files instead of querying Snowflake directly,
so the demo keeps working even when the warehouse is off.
"""

import json
from pathlib import Path

import pandas as pd

from snowflake_client import get_connection

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "app" / "data"

# One query per file. Genres are collected into a list per title.
EXPORTS = {
    "titles": """
        SELECT
            t.title_id,
            t.title,
            t.format,
            t.status,
            t.description,
            t.average_score,
            t.popularity,
            t.chapters,
            t.volumes,
            t.start_year,
            t.cover_image_url,
            t.site_url,
            ARRAY_AGG(g.genre) WITHIN GROUP (ORDER BY g.genre) AS genres
        FROM MARTS.DIM_TITLE AS t
        LEFT JOIN MARTS.BRIDGE_TITLE_GENRE AS g ON t.title_id = g.title_id
        GROUP BY ALL
    """,
    "recommendations": """
        SELECT
            title_id,
            recommended_title_id,
            recommendation_rank,
            similarity_score,
            top_shared_tags
        FROM MARTS.FCT_RECOMMENDATIONS
    """,
}

# Snowflake returns arrays as JSON text, so we turn them back into Python lists
LIST_COLUMNS = ["genres", "top_shared_tags"]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        cursor = conn.cursor()

        for name, query in EXPORTS.items():
            cursor.execute(query)
            columns = [col[0].lower() for col in cursor.description]
            df = pd.DataFrame(cursor.fetchall(), columns=columns)

            for col in LIST_COLUMNS:
                if col in df.columns:
                    df[col] = df[col].apply(lambda value: json.loads(value) if value else [])

            path = OUTPUT_DIR / f"{name}.parquet"
            df.to_parquet(path, index=False)
            print(f"Saved {len(df)} rows to {path.relative_to(OUTPUT_DIR.parents[1])}")

    print("Done")


if __name__ == "__main__":
    main()