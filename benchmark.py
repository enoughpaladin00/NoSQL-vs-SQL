import time
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

def main():
    print("Starting benchmark...")
    print("-" * 40)

    # connect to postgres
    pg_conn = psycopg2.connect(PG_URL)
    pg_cursor = pg_conn.cursor()

    # connect to memgraph
    mg_driver = GraphDatabase.driver(MG_URI, auth=(MG_USER, MG_PASS))
    mg_session = mg_driver.session()

    # ==========================================
    # TEST 1: Direct Connections (1 Hop)
    print("Test 1: Direct Connections")
    
    pg_query1 = f"SELECT dst_comp_id FROM networkevents WHERE src_comp_id = '{START_COMP}';"
    mg_query1 = f"MATCH (c1:Computer {{hostname: '{START_COMP}'}})-[:CONNECTED_TO]->(c2:Computer) RETURN c2.hostname;"

    # postgres
    start = time.time()
    pg_cursor.execute(pg_query1)
    pg_res = pg_cursor.fetchall()
    end = time.time()
    print(f"Postgres : {(end - start) * 1000:.2f} ms (found {len(pg_res)} rows)")

    # memgraph
    start = time.time()
    mg_res = list(mg_session.run(mg_query1))
    end = time.time()
    print(f"Memgraph : {(end - start) * 1000:.2f} ms (found {len(mg_res)} rows)")
    print("-" * 40)


    # ==========================================
    # TEST 2: Lateral Movement (2 Hops)
    print("Test 2: Lateral Movement (2 Hops)")

    pg_query2 = f"""
    SELECT jump2.dst_comp_id 
    FROM networkevents jump1
    JOIN networkevents jump2 ON jump1.dst_comp_id = jump2.src_comp_id
    WHERE jump1.src_comp_id = '{START_COMP}';
    """
    mg_query2 = f"MATCH (c1:Computer {{hostname: '{START_COMP}'}})-[:CONNECTED_TO*2]->(c3:Computer) RETURN c3.hostname;"

    # postgres
    start = time.time()
    pg_cursor.execute(pg_query2)
    pg_res = pg_cursor.fetchall()
    end = time.time()
    print(f"Postgres : {(end - start) * 1000:.2f} ms (found {len(pg_res)} rows)")

    # memgraph
    start = time.time()
    mg_res = list(mg_session.run(mg_query2))
    end = time.time()
    print(f"Memgraph : {(end - start) * 1000:.2f} ms (found {len(mg_res)} rows)")
    print("-" * 40)


    # ==========================================
    # TEST 3: Top 5 Active Users
    print("Test 3: Top 5 Active Users")

    pg_query3 = """
    SELECT user_id, COUNT(*) as total_events 
    FROM hostevents 
    GROUP BY user_id 
    ORDER BY total_events DESC LIMIT 5;
    """
    mg_query3 = """
    MATCH (u:User)-[r:LOGGED_ON]->(c:Computer)
    RETURN id(u) AS user_id, COUNT(r) AS total_events
    ORDER BY total_events DESC LIMIT 5;
    """

    # postgres
    start = time.time()
    pg_cursor.execute(pg_query3)
    pg_res = pg_cursor.fetchall()
    end = time.time()
    print(f"Postgres : {(end - start) * 1000:.2f} ms (found {len(pg_res)} rows)")

    # memgraph
    start = time.time()
    mg_res = list(mg_session.run(mg_query3))
    end = time.time()
    print(f"Memgraph : {(end - start) * 1000:.2f} ms (found {len(mg_res)} rows)")
    print("-" * 40)


    # ==========================================
    # TEST 4: Shortest Path (Up to 5 Hops)
    print("Test 4: Variable Shortest Path")

    pg_query4 = f"""
    WITH RECURSIVE path_search AS (
        SELECT dst_comp_id AS current_comp, 1 AS depth, 
               ARRAY[src_comp_id, dst_comp_id]::text[] AS path_array
        FROM networkevents
        WHERE src_comp_id = '{START_COMP}'
        
        UNION ALL
        
        SELECT ne.dst_comp_id, ps.depth + 1, 
               ps.path_array || ne.dst_comp_id::text
        FROM networkevents ne
        JOIN path_search ps ON ne.src_comp_id = ps.current_comp
        WHERE ps.depth < 5 AND NOT ne.dst_comp_id::text = ANY(ps.path_array)
    )
    SELECT path_array, depth
    FROM path_search
    WHERE current_comp = '{TARGET_COMP}'
    ORDER BY depth ASC LIMIT 1;
    """
    mg_query4 = f"MATCH p = (c1:Computer {{hostname: '{START_COMP}'}})-[*BFS ..5]-(c2:Computer {{hostname: '{TARGET_COMP}'}}) RETURN p;"

    # postgres
    try:
        start = time.time()
        pg_cursor.execute(pg_query4)
        pg_res = pg_cursor.fetchall()
        end = time.time()
        print(f"Postgres : {(end - start) * 1000:.2f} ms (found {len(pg_res)} rows)")
    except Exception as e:
        pg_conn.rollback()  # Reset the connection after the crash
        print(f"Postgres : FAILED / CRASHED (Disk space exhausted due to combinatorial explosion!)")

    # memgraph
    start = time.time()
    mg_res = list(mg_session.run(mg_query4))
    end = time.time()
    print(f"Memgraph : {(end - start) * 1000:.2f} ms (found {len(mg_res)} rows)")
    print("-" * 40)


    # ==========================================


    # TEST 5: Unique 2-Hop Count (Aggregated Lateral Movement)
    print("Test 5: Unique 2-Hop Count")

    pg_query5 = f"""
    SELECT COUNT(DISTINCT jump2.dst_comp_id) 
    FROM networkevents jump1
    JOIN networkevents jump2 ON jump1.dst_comp_id = jump2.src_comp_id
    WHERE jump1.src_comp_id = '{START_COMP}';
    """
    
    mg_query5 = f"MATCH (c1:Computer {{hostname: '{START_COMP}'}})-[:CONNECTED_TO*2]->(c3:Computer) RETURN COUNT(DISTINCT c3);"

    # postgres
    start = time.time()
    pg_cursor.execute(pg_query5)
    pg_res = pg_cursor.fetchall()
    end = time.time()
    print(f"Postgres : {(end - start) * 1000:.2f} ms (Result: {pg_res[0][0]} unique computers)")

    # memgraph
    start = time.time()
    mg_res = list(mg_session.run(mg_query5))
    end = time.time()
    print(f"Memgraph : {(end - start) * 1000:.2f} ms (Result: {mg_res[0][0]} unique computers)")
    print("-" * 40)


    # close connections
    pg_cursor.close()
    pg_conn.close()
    mg_session.close()
    mg_driver.close()
    
    print("Benchmark finished.")

if __name__ == "__main__":
    main()