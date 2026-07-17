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

2. **Start the databases:**
   Use Docker Compose to spin up PostgreSQL and MemGraph:
   ```bash
   docker-compose up -d
   ```
   *Note: PostgreSQL runs on port `5433`, MemGraph runs on `7687`, and MemGraph Lab (UI) runs on `3000`.*

3. **Set up Python Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

## Dataset
Because the LANL dataset is massive, the `data/` directory is ignored by Git. We are currently using **day 02** and **day 04** of the dataset for our tests.

To download the dataset automatically, run the included script (this will download `wls_day-02.bz2`, `wls_day-04.bz2`, `netflow_day-02.bz2`, and `netflow_day-04.bz2`):
```bash
bash scripts/download_data.sh
```

## Running the Code
*(WIP - Scripts are currently being developed)*
- **`src/schema.py`**: Initializes the database schemas.
- **`src/ingest_data.py`**: Loads the LANL dataset into both PostgreSQL and MemGraph (currently limited to 1 million rows for development).
- **`src/benchmark.py`**: Runs benchmark queries and records execution time.
