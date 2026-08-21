<!--
# Benchmark Queries: PostgreSQL vs Memgraph
This document contains the set of queries designed to analyze the performance of our relational database (PostgreSQL) against our graph database (Memgraph). 

The goal of this benchmark is to prove how SQL and Cypher handle different types of data retrieval, highlighting the complexity and execution times when dealing with relational aggregations versus complex pathfinding (Lateral Movement) in a cybersecurity context.

---

## Test 1: Direct Connections (1 Hop)
**Objective:** Find all computers directly connected to a specific starting computer.

**PostgreSQL (SQL):**
SELECT destination_computer 
FROM network_events 
WHERE source_computer = 'START_COMPUTER';

**Memgraph**
MATCH (c1:Computer {name: 'START_COMPUTER'})-[:NETWORK_CONNECTION]->(c2:Computer)
RETURN c2.name;



## Test 2: Lateral Movement (2 Hops)
**Objective:** Trace a 2-hop connection (Computer A -> Computer B -> Computer C) to discover the final destination (C).

**PostgreSQL (SQL):**
SELECT jump2.destination_computer 
FROM network_events jump1
JOIN network_events jump2 ON jump1.destination_computer = jump2.source_computer
WHERE jump1.source_computer = 'START_COMPUTER';

**Memgraph**
MATCH (c1:Computer {name: 'START_COMPUTER'})-[:NETWORK_CONNECTION*2]->(c3:Computer)
RETURN c3.name;



## Test 3: Top 5 Active Users 
**Objective:** Identify the top 5 users with the highest number of logon events.

**PostgreSQL (SQL):**
SELECT user_id, COUNT(*) as total_logons 
FROM host_events 
WHERE event_type = 'LogOn'
GROUP BY user_id 
ORDER BY total_logons DESC 
LIMIT 5;

**Memgraph:**
MATCH (u:User)-[r:LOGON]->(c:Computer)
RETURN u.name AS user_id, COUNT(r) AS total_logons
ORDER BY total_logons DESC
LIMIT 5;



## Test 4: Variable Shortest Path (Up to 5 Hops)
**Objective:** Find the shortest path between a Start Computer and a Target Computer, regardless of the exact number of steps (from 1 up to 5 hops).

**PostgreSQL (SQL):**
WITH RECURSIVE path_search AS (
    -- Base case: First hop from the starting computer
    SELECT destination_computer AS current_comp,
           1 AS depth,
           ARRAY[source_computer, destination_computer] AS path
    FROM network_events
    WHERE source_computer = 'START_COMPUTER'

    UNION ALL

    -- Recursive step: Jump to the next connected computers
    SELECT ne.destination_computer,
           ps.depth + 1,
           ps.path || ne.destination_computer
    FROM network_events ne
    JOIN path_search ps ON ne.source_computer = ps.current_comp
    WHERE ps.depth < 5
      AND NOT ne.destination_computer = ANY(ps.path) -- Cycle prevention
)
SELECT path
FROM path_search
WHERE current_comp = 'TARGET_COMPUTER'
ORDER BY depth ASC
LIMIT 1;

**Memgraph:**
MATCH p = shortestPath((c1:Computer {name: 'START_COMPUTER'})-[*..5]-(c2:Computer {name: 'TARGET_COMPUTER'}))
RETURN p;

-->
# Benchmark Queries: PostgreSQL vs Memgraph
This document contains the set of queries designed to analyze the performance of our relational database (PostgreSQL) against our graph database (Memgraph). 

The goal of this benchmark is to prove how SQL and Cypher handle different types of data retrieval, highlighting the complexity and execution times when dealing with relational aggregations versus complex pathfinding (Lateral Movement) in a cybersecurity context.

---

## Test 1: Direct Connections (1 Hop)
**Objective:** Find all computers directly connected to a specific starting computer.

**PostgreSQL (SQL):**
SELECT dst_comp_id 
FROM networkevents 
WHERE src_comp_id = 'Comp107130';

**Memgraph:**
MATCH (c1:Computer {hostname: 'Comp107130'})-[:CONNECTED_TO]->(c2:Computer)
RETURN c2.hostname;

---

## Test 2: Lateral Movement (2 Hops)
**Objective:** Trace a 2-hop connection (Computer A -> Computer B -> Computer C) to discover the final destination (C).

**PostgreSQL (SQL):**
SELECT jump2.dst_comp_id 
FROM networkevents jump1
JOIN networkevents jump2 ON jump1.dst_comp_id = jump2.src_comp_id
WHERE jump1.src_comp_id = 'Comp107130';

**Memgraph:**
MATCH (c1:Computer {hostname: 'Comp107130'})-[:CONNECTED_TO*2]->(c3:Computer)
RETURN c3.hostname;

---

## Test 3: Top 5 Active Users 
**Objective:** Identify the top 5 users with the highest number of events.

**PostgreSQL (SQL):**
SELECT user_id, COUNT(*) as total_events 
FROM hostevents 
GROUP BY user_id 
ORDER BY total_events DESC 
LIMIT 5;

**Memgraph:**
MATCH (u:User)-[r:LOGGED_ON]->(c:Computer)
RETURN id(u) AS user_id, COUNT(r) AS total_events
ORDER BY total_events DESC
LIMIT 5;

---

## Test 4: Variable Shortest Path (Up to 5 Hops)
**Objective:** Find the shortest path between a Start Computer and a Target Computer, regardless of the exact number of steps.

**PostgreSQL (SQL):**
WITH RECURSIVE path_search AS (
    -- Base case: First hop
    SELECT dst_comp_id AS current_comp,
           1 AS depth,
           ARRAY[src_comp_id, dst_comp_id] AS path
    FROM networkevents
    WHERE src_comp_id = 'Comp107130'

    UNION ALL

    -- Recursive step: Next hops
    SELECT ne.dst_comp_id,
           ps.depth + 1,
           ps.path || ne.dst_comp_id
    FROM networkevents ne
    JOIN path_search ps ON ne.src_comp_id = ps.current_comp
    WHERE ps.depth < 5
      AND NOT ne.dst_comp_id = ANY(ps.path)
)
SELECT path
FROM path_search
WHERE current_comp = 'Comp916004'
ORDER BY depth ASC
LIMIT 1;

**Memgraph:**
MATCH p = (c1:Computer {hostname: 'Comp107130'})-[*BFS ..5]-(c2:Computer {hostname: 'Comp916004'})
RETURN p;