import time
import os
import json
import psycopg2
from neo4j import GraphDatabase

# Connessioni definitive scoperte dal docker-compose
PG_URL = "postgresql://postgres:password@localhost:5433/dm_project"
MG_URI = "bolt://localhost:7687"
MG_USER = ""
MG_PASS = ""

# Nodi reali per i test
START_COMP = "Comp107130" 
TARGET_COMP = "Comp916004"

ITERATIONS = 5

def run_postgres_test(cursor, query_name, query, is_recursive=False):
    times = []
    rows_found = 0
    for i in range(ITERATIONS):
        try:
            start = time.time()
            cursor.execute(query)
            res = cursor.fetchall()
            end = time.time()
            times.append((end - start) * 1000)
            rows_found = len(res)
        except Exception as e:
            cursor.connection.rollback()
            print(f"  -> Postgres {query_name} FAILED / CRASHED")
            return None
    
    avg_time = sum(times) / len(times)
    print(f"  -> {query_name}: {avg_time:.2f} ms (avg over {ITERATIONS} runs, found {rows_found} rows)")
    return avg_time

def run_memgraph_test(session, query_name, query):
    times = []
    rows_found = 0
    for i in range(ITERATIONS):
        start = time.time()
        res = list(session.run(query))
        end = time.time()
        times.append((end - start) * 1000)
        rows_found = len(res)
    
    avg_time = sum(times) / len(times)
    print(f"  -> {query_name}: {avg_time:.2f} ms (avg over {ITERATIONS} runs, found {rows_found} rows)")
    return avg_time

def main():
    print("Starting comprehensive benchmark (Averaging over 5 runs)...")
    print("-" * 40)
    os.makedirs("results", exist_ok=True)
    results = {
        "Test 1: Direct Connections": {},
        "Test 2: Lateral Movement (2 Hops)": {},
        "Test 3: Top 5 Active Users": {},
        "Test 4: Variable Shortest Path": {},
        "Test 5: Unique 2-Hop Count": {}
    }

    # connect to postgres
    pg_conn = psycopg2.connect(PG_URL)
    pg_conn.autocommit = True
    pg_cursor = pg_conn.cursor()
    
    # Add a strict 15-second timeout to prevent Recursive CTE from blowing up the disk!
    pg_cursor.execute("SET statement_timeout = 15000;")

    # connect to memgraph
    mg_driver = GraphDatabase.driver(MG_URI, auth=(MG_USER, MG_PASS))
    mg_session = mg_driver.session()

    # DEFINITION OF QUERIES
    tests = {
        "Test 1: Direct Connections": {
            "pg": f"SELECT dst_comp_id FROM networkevents WHERE src_comp_id = '{START_COMP}';",
            "mg": f"MATCH (c1:Computer {{hostname: '{START_COMP}'}})-[:CONNECTED_TO]->(c2:Computer) RETURN c2.hostname;"
        },
        "Test 2: Lateral Movement (2 Hops)": {
            "pg": f"SELECT jump2.dst_comp_id FROM networkevents jump1 JOIN networkevents jump2 ON jump1.dst_comp_id = jump2.src_comp_id WHERE jump1.src_comp_id = '{START_COMP}';",
            "mg": f"MATCH (c1:Computer {{hostname: '{START_COMP}'}})-[:CONNECTED_TO*2]->(c3:Computer) RETURN c3.hostname;"
        },
        "Test 3: Top 5 Active Users": {
            "pg": "SELECT user_id, COUNT(*) as total_events FROM hostevents GROUP BY user_id ORDER BY total_events DESC LIMIT 5;",
            "mg": "MATCH (u:User)-[r:LOGGED_ON]->(c:Computer) RETURN id(u) AS user_id, COUNT(r) AS total_events ORDER BY total_events DESC LIMIT 5;"
        },
        "Test 4: Variable Shortest Path": {
            "pg": f"WITH RECURSIVE path_search AS (SELECT dst_comp_id AS current_comp, 1 AS depth, ARRAY[src_comp_id, dst_comp_id]::text[] AS path_array FROM networkevents WHERE src_comp_id = '{START_COMP}' UNION ALL SELECT ne.dst_comp_id, ps.depth + 1, ps.path_array || ne.dst_comp_id::text FROM networkevents ne JOIN path_search ps ON ne.src_comp_id = ps.current_comp WHERE ps.depth < 5 AND NOT ne.dst_comp_id::text = ANY(ps.path_array)) SELECT path_array, depth FROM path_search WHERE current_comp = '{TARGET_COMP}' ORDER BY depth ASC LIMIT 1;",
            "mg": f"MATCH p = (c1:Computer {{hostname: '{START_COMP}'}})-[*BFS ..5]-(c2:Computer {{hostname: '{TARGET_COMP}'}}) RETURN p;"
        },
        "Test 5: Unique 2-Hop Count": {
            "pg": f"SELECT COUNT(DISTINCT jump2.dst_comp_id) FROM networkevents jump1 JOIN networkevents jump2 ON jump1.dst_comp_id = jump2.src_comp_id WHERE jump1.src_comp_id = '{START_COMP}';",
            "mg": f"MATCH (c1:Computer {{hostname: '{START_COMP}'}})-[:CONNECTED_TO*2]->(c3:Computer) RETURN COUNT(DISTINCT c3);"
        }
    }

    # ==========================================
    print("PHASE 1: PostgreSQL (Unindexed)")
    for test_name, queries in tests.items():
        if test_name == "Test 4: Variable Shortest Path":
            print("  -> SKIPPING Test 4 for Unindexed Postgres (Causes Docker Disk Overflow due to combinatorial explosion!)")
            results[test_name]["PostgreSQL (Unindexed)"] = None
            continue
            
        print(f"Running {test_name}...")
        avg_time = run_postgres_test(pg_cursor, test_name, queries["pg"], is_recursive=False)
        results[test_name]["PostgreSQL (Unindexed)"] = avg_time
    print("-" * 40)

    # ==========================================
    print("PHASE 2: Creating PostgreSQL Indices")
    idx_queries = [
        "CREATE INDEX IF NOT EXISTS idx_ne_src ON networkevents(src_comp_id);",
        "CREATE INDEX IF NOT EXISTS idx_ne_dst ON networkevents(dst_comp_id);",
        "CREATE INDEX IF NOT EXISTS idx_he_user ON hostevents(user_id);"
    ]
    for q in idx_queries:
        pg_cursor.execute(q)
    print("Indices created successfully!")
    print("-" * 40)

    # ==========================================
    print("PHASE 3: PostgreSQL (Indexed)")
    for test_name, queries in tests.items():
        print(f"Running {test_name}...")
        avg_time = run_postgres_test(pg_cursor, test_name, queries["pg"], is_recursive=(test_name == "Test 4: Variable Shortest Path"))
        results[test_name]["PostgreSQL (Indexed)"] = avg_time
    print("-" * 40)

    # ==========================================
    print("PHASE 4: Memgraph (Native Graph with Uniqueness Indices)")
    for test_name, queries in tests.items():
        print(f"Running {test_name}...")
        avg_time = run_memgraph_test(mg_session, test_name, queries["mg"])
        results[test_name]["Memgraph"] = avg_time
    print("-" * 40)

    # Saving Results
    with open("results/benchmark_stats.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Saved results to results/benchmark_stats.json")

    # close connections
    pg_cursor.close()
    pg_conn.close()
    mg_session.close()
    mg_driver.close()
    
    print("Benchmark finished.")

if __name__ == "__main__":
    main()
