from snowflake_client import get_connection

with get_connection() as conn:
    cur = conn.cursor()
    cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE()")
    print("Connected to Snowflake", cur.fetchone())