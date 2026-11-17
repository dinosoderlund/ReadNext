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
PAGES_TO_FETCH = 20 # 20 pages x 50 titles = 1 000 titles
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