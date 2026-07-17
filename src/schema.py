import os
import psycopg2
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL Connection settings
PG_URL = os.getenv("DATABASE_URL")

# MemGraph Connection settings
MG_URI = os.getenv("MEMGRAPH_URI")
MG_USER = os.getenv("MEMGRAPH_USER", "")
MG_PASSWORD = os.getenv("MEMGRAPH_PASSWORD", "")

def init_postgres():
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(PG_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    print("Dropping existing tables if they exist...")
    cursor.execute("DROP TABLE IF EXISTS NetworkEvents CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS HostEvents CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS Computers CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS Users CASCADE;")

    print("Creating PostgreSQL schemas...")
    
    # Create Users table
    cursor.execute("""
        CREATE TABLE Users (
            id VARCHAR(255) PRIMARY KEY,
            domain_name VARCHAR(255)
        );
    """)

    # Create Computers table
    cursor.execute("""
        CREATE TABLE Computers (
            id VARCHAR(255) PRIMARY KEY
        );
    """)

    # Create HostEvents table
    cursor.execute("""
        CREATE TABLE HostEvents (
            id SERIAL PRIMARY KEY,
            time INTEGER,
            user_id VARCHAR(255) REFERENCES Users(id),
            computer_id VARCHAR(255) REFERENCES Computers(id),
            event_id INTEGER,
            logon_type INTEGER
        );
    """)

    # Create NetworkEvents table
    cursor.execute("""
        CREATE TABLE NetworkEvents (
            id SERIAL PRIMARY KEY,
            time INTEGER,
            src_comp_id VARCHAR(255) REFERENCES Computers(id),
            dst_comp_id VARCHAR(255) REFERENCES Computers(id),
            protocol INTEGER,
            src_port VARCHAR(255),
            dst_port VARCHAR(255),
            duration INTEGER,
            src_bytes BIGINT,
            dst_bytes BIGINT
        );
    """)

    print("PostgreSQL schema initialization complete.")
    cursor.close()
    conn.close()

def init_memgraph():
    print("Connecting to Memgraph...")
    driver = GraphDatabase.driver(MG_URI, auth=(MG_USER, MG_PASSWORD))
    
    with driver.session() as session:
        print("Cleaning up existing graph data (optional, for fresh start)...")
        session.run("MATCH (n) DETACH DELETE n;")

        print("Creating Memgraph constraints/indexes...")
        # Create unique constraints (which automatically create indexes in Memgraph)
        try:
            session.run("CREATE CONSTRAINT ON (u:User) ASSERT u.username IS UNIQUE;")
        except Exception as e:
            print("Constraint User.username already exists or error:", e)

        try:
            session.run("CREATE CONSTRAINT ON (c:Computer) ASSERT c.hostname IS UNIQUE;")
        except Exception as e:
            print("Constraint Computer.hostname already exists or error:", e)

    driver.close()
    print("Memgraph schema initialization complete.")

if __name__ == "__main__":
    init_postgres()
    init_memgraph()
    print("All schemas successfully initialized!")
