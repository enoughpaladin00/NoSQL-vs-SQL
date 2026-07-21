#!/bin/bash

# Main script to manage the Data Management Project

function usage() {
    echo "Usage: ./run.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup       - Create virtual environment and install dependencies"
    echo "  download    - Download the LANL dataset files"
    echo "  start       - Start PostgreSQL and Memgraph via Docker Compose"
    echo "  stop        - Stop the Docker containers"
    echo "  schema      - Initialize database schemas in PostgreSQL and Memgraph"
    echo "  ingest      - Run the data ingestion script"
    echo "  psql        - Open an interactive PostgreSQL terminal"
    echo "  benchmark   - Run the benchmark queries script"
}

COMMAND=$1

case $COMMAND in
    setup)
        echo "Setting up Python virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        echo "Setup complete. If you haven't already, run: cp .env.example .env"
        ;;
    download)
        echo "Starting dataset download..."
        bash scripts/download_data.sh
        ;;
    start)
        echo "Starting database containers..."
        docker-compose up -d
        ;;
    stop)
        echo "Stopping database containers..."
        docker-compose down
        ;;
    schema)
        echo "Initializing schemas..."
        venv/bin/python src/schema.py
        ;;
    ingest)
        echo "Starting data ingestion..."
        venv/bin/python src/ingest_data.py
        ;;
    psql)
        echo "Connecting to PostgreSQL interactive terminal..."
        docker exec -it dm_postgres psql -U postgres -d dm_project
        ;;
    benchmark)
        echo "Running benchmarks..."
        venv/bin/python src/benchmark.py
        ;;
    *)
        usage
        ;;
esac
