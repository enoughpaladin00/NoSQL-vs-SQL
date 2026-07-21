import os
import bz2
import json
import csv
import psycopg2
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

PG_URL = os.getenv("DATABASE_URL")
MG_URI = os.getenv("MEMGRAPH_URI")
MG_USER = os.getenv("MEMGRAPH_USER", "")
MG_PASSWORD = os.getenv("MEMGRAPH_PASSWORD", "")

# We will limit to 1 million rows per file for development
ROW_LIMIT = 1_000_000
BATCH_SIZE = 5_000

def process_host_events(pg_conn, mg_driver):
    print("Processing Host Events...")
    pg_cursor = pg_conn.cursor()
    
    file_path = "data/HostEvent/wls_day-02.bz2"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Skipping...")
        return

    users_batch = set()
    computers_batch = set()
    host_events_batch = []
    
    count = 0
    with bz2.open(file_path, "rt") as f, mg_driver.session() as mg_session:
        for line in f:
            if count >= ROW_LIMIT:
                break
                
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            time = event.get("Time")
            user_id = event.get("UserName")
            domain_name = event.get("DomainName")
            log_host = event.get("LogHost")
            source = event.get("Source", log_host) # Default to log_host if missing
            event_id = event.get("EventID")
            logon_type = event.get("LogonType")
            logon_type_desc = event.get("LogonTypeDescription")
            logon_id = event.get("LogonID")
            subject_user_id = event.get("SubjectUserName")
            subject_logon_id = event.get("SubjectLogonID")
            status = event.get("Status")
            service_name = event.get("ServiceName")
            destination = event.get("Destination")
            auth_package = event.get("AuthenticationPackage")
            failure_reason = event.get("FailureReason")
            process_name = event.get("ProcessName")
            process_id = event.get("ProcessID")
            parent_process_name = event.get("ParentProcessName")
            parent_process_id = event.get("ParentProcessID")

            if user_id:
                users_batch.add((user_id, domain_name))
            if log_host:
                computers_batch.add(log_host)
            if source:
                computers_batch.add(source)

            host_events_batch.append((
                time, event_id, log_host, logon_type, logon_type_desc, user_id, logon_id,
                subject_user_id, subject_logon_id, status, source, service_name,
                destination, auth_package, failure_reason, process_name, process_id,
                parent_process_name, parent_process_id
            ))

            count += 1
            if count % BATCH_SIZE == 0:
                _insert_host_batch(pg_cursor, mg_session, users_batch, computers_batch, host_events_batch)
                users_batch.clear()
                computers_batch.clear()
                host_events_batch.clear()
                print(f"Processed {count} Host Events...")

        if host_events_batch:
            _insert_host_batch(pg_cursor, mg_session, users_batch, computers_batch, host_events_batch)
            print(f"Processed {count} Host Events (Final Batch)")

    pg_cursor.close()

def _insert_host_batch(pg_cursor, mg_session, users, computers, events):
    # PostgreSQL Inserts
    if users:
        pg_cursor.executemany(
            "INSERT INTO Users (id, domain_name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING;",
            list(users)
        )
    if computers:
        pg_cursor.executemany(
            "INSERT INTO Computers (id) VALUES (%s) ON CONFLICT (id) DO NOTHING;",
            [(c,) for c in computers]
        )
    if events:
        pg_cursor.executemany("""
            INSERT INTO HostEvents (
                time, event_id, computer_id, logon_type, logon_type_description,
                user_id, logon_id, subject_user_id, subject_logon_id, status,
                source_computer_id, service_name, destination, authentication_package,
                failure_reason, process_name, process_id, parent_process_name, parent_process_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
        """, events)

    # Memgraph Inserts using UNWIND for batch processing
    if users:
        mg_session.run("""
            UNWIND $users AS u
            MERGE (user:User {username: u[0]})
            ON CREATE SET user.domain = u[1]
        """, users=list(users))
        
    if computers:
        mg_session.run("""
            UNWIND $comps AS c
            MERGE (:Computer {hostname: c})
        """, comps=list(computers))
        
    if events:
        # Simplify the edge to just basic properties to avoid massive payloads, or include all
        # We'll map (User)-[:LOGGED_ON]->(Computer) and (Source)-[:AUTH_TO]->(Computer)
        mg_session.run("""
            UNWIND $events AS e
            MATCH (u:User {username: e[5]})
            MATCH (c:Computer {hostname: e[2]})
            CREATE (u)-[:LOGGED_ON {
                time: e[0], event_id: e[1], logon_type: e[3], status: e[9]
            }]->(c)
        """, events=[e for e in events if e[5] and e[2]])
        
        # Create an edge between source computer and log host if they differ (lateral movement)
        mg_session.run("""
            UNWIND $events AS e
            MATCH (src:Computer {hostname: e[10]})
            MATCH (dst:Computer {hostname: e[2]})
            WITH src, dst, e WHERE src.hostname <> dst.hostname
            CREATE (src)-[:AUTH_TO {
                time: e[0], user: e[5], event_id: e[1], logon_type: e[3]
            }]->(dst)
        """, events=[e for e in events if e[2] and e[10]])


def process_network_events(pg_conn, mg_driver):
    print("Processing Network Events...")
    pg_cursor = pg_conn.cursor()
    
    file_path = "data/NetFlow/netflow_day-02.bz2"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Skipping...")
        return

    computers_batch = set()
    net_events_batch = []
    
    count = 0
    with bz2.open(file_path, "rt") as f, mg_driver.session() as mg_session:
        reader = csv.reader(f)
        for row in reader:
            if count >= ROW_LIMIT:
                break
                
            if len(row) < 11:
                continue

            # Time, Duration, SrcDevice, DstDevice, Protocol, SrcPort, DstPort, SrcPackets, DstPackets, SrcBytes, DstBytes
            time = int(row[0]) if row[0] else None
            duration = int(row[1]) if row[1] else None
            src_comp = row[2]
            dst_comp = row[3]
            protocol = int(row[4]) if row[4] else None
            src_port = row[5]
            dst_port = row[6]
            src_packets = int(row[7]) if row[7] else None
            dst_packets = int(row[8]) if row[8] else None
            src_bytes = int(row[9]) if row[9] else None
            dst_bytes = int(row[10]) if row[10] else None

            if src_comp:
                computers_batch.add(src_comp)
            if dst_comp:
                computers_batch.add(dst_comp)

            net_events_batch.append((
                time, src_comp, dst_comp, protocol, src_port, dst_port,
                duration, src_packets, dst_packets, src_bytes, dst_bytes
            ))

            count += 1
            if count % BATCH_SIZE == 0:
                _insert_net_batch(pg_cursor, mg_session, computers_batch, net_events_batch)
                computers_batch.clear()
                net_events_batch.clear()
                print(f"Processed {count} Network Events...")

        if net_events_batch:
            _insert_net_batch(pg_cursor, mg_session, computers_batch, net_events_batch)
            print(f"Processed {count} Network Events (Final Batch)")

    pg_cursor.close()

def _insert_net_batch(pg_cursor, mg_session, computers, events):
    if computers:
        pg_cursor.executemany(
            "INSERT INTO Computers (id) VALUES (%s) ON CONFLICT (id) DO NOTHING;",
            [(c,) for c in computers]
        )
        
    if events:
        pg_cursor.executemany("""
            INSERT INTO NetworkEvents (
                time, src_comp_id, dst_comp_id, protocol, src_port, dst_port,
                duration, src_packets, dst_packets, src_bytes, dst_bytes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            );
        """, events)

    # Memgraph Inserts
    if computers:
        mg_session.run("""
            UNWIND $comps AS c
            MERGE (:Computer {hostname: c})
        """, comps=list(computers))
        
    if events:
        mg_session.run("""
            UNWIND $events AS e
            MATCH (src:Computer {hostname: e[1]})
            MATCH (dst:Computer {hostname: e[2]})
            CREATE (src)-[:CONNECTED_TO {
                time: e[0], protocol: e[3], src_port: e[4], dst_port: e[5],
                duration: e[6], src_packets: e[7], dst_packets: e[8],
                src_bytes: e[9], dst_bytes: e[10]
            }]->(dst)
        """, events=[e for e in events if e[1] and e[2]])

if __name__ == "__main__":
    print("Connecting to databases...")
    pg_conn = psycopg2.connect(PG_URL)
    pg_conn.autocommit = True
    mg_driver = GraphDatabase.driver(MG_URI, auth=(MG_USER, MG_PASSWORD))
    
    process_host_events(pg_conn, mg_driver)
    process_network_events(pg_conn, mg_driver)
    
    pg_conn.close()
    mg_driver.close()
    print("Ingestion complete!")
