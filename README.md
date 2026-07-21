# Data Management Project: NoSQL vs Relational DBMS

This project compares the performance of a Relational Database (PostgreSQL) and a Graph Database (MemGraph) when handling highly interconnected data. We use the [Unified Host and Network Dataset](https://csr.lanl.gov/data/2017/) from Los Alamos National Laboratory to simulate a large enterprise network.

## Project Goal
We extract **Users** and **Computers** as nodes (or tables) and **Network Connections / Logons** as edges (or relationships with foreign keys) to compare query execution times, particularly for pathfinding queries like finding the shortest path a user can take to jump from one computer to another.

## Requirements
- Docker and Docker Compose
- Python 3.10+
- `venv` for Python package management

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd "Data Management/Project"
   ```

2. **Environment Setup:**
   Create the virtual environment, install dependencies, and set up your `.env` file with a single command:
   ```bash
   ./run.sh setup
   ```

3. **Start the databases:**
   Use Docker Compose to spin up PostgreSQL and MemGraph:
   ```bash
   ./run.sh start
   ```
   *Note: PostgreSQL runs on port `5433`, MemGraph runs on `7687`, and MemGraph Lab (UI) runs on `3000`.*

## Dataset
Because the LANL dataset is massive, the `data/` directory is ignored by Git. We are currently using **day 02** and **day 04** of the dataset for our tests.

To download the dataset automatically, run:
```bash
./run.sh download
```

## Running the Code

Use the `run.sh` script to manage the database schema and data ingestion:

1. **Initialize Schemas:**
   ```bash
   ./run.sh schema
   ```
2. **Ingest Data:**
   ```bash
   ./run.sh ingest
   ```
   *(Note: Currently limited to 1 million rows for development purposes.)*

## Exploring the Data

**PostgreSQL:**
You can quickly drop into an interactive SQL terminal to query Postgres by running:
```bash
./run.sh psql
```
*(Type `\q` to exit).*

**Memgraph (Graph UI):**
1. Open your web browser and navigate to **http://localhost:3000**.
2. Click **New Connection** (do not use Quick Connect).
3. Set the **Host** to `dm_memgraph` (this is the internal Docker name).
4. Leave the port as `7687` and keep username/password completely blank.
5. Click **Connect** to access the visual graph Dashboard!
