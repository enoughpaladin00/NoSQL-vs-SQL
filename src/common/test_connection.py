import os
import psycopg2
from neo4j import GraphDatabase

# Local defaults
PG_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/dm_project")
MG_URI = os.getenv("MEMGRAPH_URI", "bolt://localhost:7687")

def test_postgres():
    try:
        conn = psycopg2.connect(PG_URL)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✅ Successfully connected to PostgreSQL:\n   {version}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")

def test_memgraph():
    try:
        driver = GraphDatabase.driver(MG_URI, auth=("", ""))
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS cnt;")
            count = result.single()[0]
            print(f"✅ Successfully connected to Memgraph!\n   Node count: {count}")
        driver.close()
    except Exception as e:
        print(f"❌ Failed to connect to Memgraph: {e}")

if __name__ == "__main__":
    print("Testing database connections...\n")
    test_postgres()
    print("-" * 40)
    test_memgraph()
