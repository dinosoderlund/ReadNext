"""
Fetch manga and light novels from Anilist and save them in snowflake(Raw)
Run from the project root:
    python ingestion/anilist_to_raw.py
"""
import json 
import time 
import requests
from snowflake_client import get_connection

ANILIST_URL = "https://graphql.anilist.co"
PAGES_TO_FETCH = 200 # 200 pages x 50 titles = 1 0000 titles
TITLES_PER_PAGE = 50 # 50 is the maximum Anilist allows 
WAIT_SECONDS = 2 # to stay under the rate limit 

# The graphQL query: which titles we want and which fields to get back 
QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage }
    media(type: MANGA, format_in: [MANGA, NOVEL], isAdult: false, sort: POPULARITY_DESC) {
      id
      title { romaji english }
      format
      status
      description(asHtml: false)
      genres
      tags { name rank }
      averageScore
      popularity
      chapters
      volumes
      startDate { year }
      coverImage { large }
      siteUrl
    }
  }
}
"""

# get one page of titles from anilist 

def fetch_page(page):
    variables = {"page": page, "perPage": TITLES_PER_PAGE}
    response = requests.post(ANILIST_URL, json={"query": QUERY, "variables": variables})

    # 429 = we sent too many requests
    if response.status_code == 429:
        wait = int(response.headers.get("Retry-After", 60))
        print(f"to many requests waiting {wait} seconds")
        time.sleep(wait)
        return fetch_page(page)

    response.raise_for_status() # exception for other type of errors 
    return response.json()["data"]["Page"]


# save the titles in snowflake
def save_titles(cursor, titles):
    """
    We send the whole page(50 titles) as one whole json list.
    Flattens slits the list into one row per title inside snowflake.
    Merge = insert the title if new, update if it already exists to avoid duplicates
    """
    cursor.execute("""
        MERGE INTO RAW.ANILIST_MEDIA AS target
        USING (
            SELECT value:id::NUMBER AS id, value AS payload
            FROM TABLE(FLATTEN(input => PARSE_JSON(%s)))
        ) AS source
        ON target.id = source.id
        WHEN MATCHED THEN UPDATE SET
            payload = source.payload,
            loaded_at = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN INSERT (id, payload, loaded_at)
            VALUES (source.id, source.payload, CURRENT_TIMESTAMP())
        """,
        (json.dumps(titles),),
        )

# run everything 
def main():
    with get_connection() as conn:
        cursor = conn.cursor()

        # create the table the first time we run the script
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RAW.ANILIST_MEDIA (
                id        NUMBER PRIMARY KEY,
                payload   VARIANT,
                loaded_at TIMESTAMP
            )
            """
        )
        
        
        for page in range(1, PAGES_TO_FETCH + 1):
          data = fetch_page(page)
          save_titles(cursor, data["media"])
          print(f"Page {page}: saved {len(data["media"])} titles")
          
          if not data["pageInfo"]["hasNextPage"]:
            break # no more titles to fetch
          time.sleep(WAIT_SECONDS)
        
        cursor.execute("SELECT COUNT(*) FROM RAW.ANILIST_MEDIA")
        print(f"Done, the table now has {cursor.fetchone()[0]} titles")


if __name__ == "__main__":
  main()