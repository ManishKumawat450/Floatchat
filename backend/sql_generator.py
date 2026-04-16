import os
from groq import Groq
from dotenv import load_dotenv
import psycopg2

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DB_SCHEMA = """
Table: argo_profiles
Columns:
- id (integer)
- float_id (varchar) — Argo float unique ID
- date (timestamp) — Measurement date/time
- latitude (float) — Float latitude (0 to 26 = India region)
- longitude (float) — Float longitude (55 to 101 = India region)
- pressure (float) — Depth in dbar
- temperature (float) — Ocean temperature in Celsius
- salinity (float) — Ocean salinity in PSU
- data_centre (varchar) — Institution code
- platform_type (varchar) — Float type
- project_name (varchar) — Project name

Table: float_metadata
Columns:
- float_id (varchar) — Unique float ID
- data_centre (varchar) — Institution
- first_seen (timestamp) — First recorded date
- last_seen (timestamp) — Last recorded date
- total_profiles (integer) — Total profiles count

Important notes:
- Arabian Sea = latitude 8-26, longitude 55-78
- Bay of Bengal = latitude 5-22, longitude 80-101
- Indian Ocean = latitude 0-26, longitude 55-101
- Depth = pressure (1 dbar = ~1 meter)
"""

def generate_sql(user_query: str) -> dict:
    prompt = f"""You are an expert oceanographic data analyst.
Convert the user's natural language query into a PostgreSQL SQL query.

Database Schema:
{DB_SCHEMA}

Rules:
1. Always return valid PostgreSQL SQL only
2. Use LIMIT 1000 to avoid huge results
3. Always alias aggregated columns properly:
   - AVG(temperature) AS avg_temperature
   - AVG(salinity) AS avg_salinity
   - COUNT(*) AS count
   - COUNT(DISTINCT float_id) AS count
4. For location queries use latitude/longitude ranges
5. Always include date in results when possible
6. Return ONLY the SQL query — no explanation no markdown
7. IMPORTANT: Date format in user queries is DD-MM-YYYY
   So 01-03-2026 means Day=01, Month=03, Year=2026 = March 1st 2026
   And 15-06-2024 means Day=15, Month=06, Year=2024 = June 15th 2024
   For specific date queries NEVER use date = 'YYYY-MM-DD'
   Always convert DD-MM-YYYY to proper range:
   date >= 'YYYY-MM-DD' AND date < 'YYYY-MM-DD+1day'
   Example: 01-03-2026 → date >= '2026-03-01' AND date < '2026-03-02'
   Example: 15-06-2024 → date >= '2024-06-15' AND date < '2024-06-16'
8. For year queries use EXTRACT(YEAR FROM date) = YYYY
9. For month queries use EXTRACT(MONTH FROM date) = MM AND EXTRACT(YEAR FROM date) = YYYY

User Query: {user_query}

SQL Query:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500
    )

    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return {"user_query": user_query, "sql": sql}


def run_query(sql: str) -> list:
    try:
        conn = psycopg2.connect(
            host     = os.getenv("DB_HOST"),
            port     = os.getenv("DB_PORT"),
            dbname   = os.getenv("DB_NAME"),
            user     = os.getenv("DB_USER"),
            password = os.getenv("DB_PASSWORD")
        )
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        return [{"error": str(e)}]


def explain_result(user_query: str, sql: str, result: list) -> str:
    prompt = f"""You are a friendly oceanographic data assistant.
The user asked: "{user_query}"
SQL used: {sql}
Data result: {result[:5]}

Give a clear, simple answer in 2-3 sentences.
Include the actual numbers from the result.
Be conversational and helpful."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()


def ask_floatchat(user_query: str) -> dict:
    print(f"\nUser: {user_query}")

    result = generate_sql(user_query)
    sql = result['sql']
    print(f"SQL: {sql}")

    db_result = run_query(sql)
    print(f"DB Result: {db_result[:3]}")

    answer = explain_result(user_query, sql, db_result)
    print(f"Answer: {answer}")

    return {
        "query" : user_query,
        "sql"   : sql,
        "data"  : db_result,
        "answer": answer
    }


if __name__ == "__main__":
    ask_floatchat("What is the average temperature in Arabian Sea in 2023?")
    ask_floatchat("How many floats are in the Indian Ocean?")
    ask_floatchat("Show salinity profiles near equator in January 2024")