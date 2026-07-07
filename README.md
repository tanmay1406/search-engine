# Distributed Search Engine

A distributed search engine built using gRPC that dynamically replicates search indices based on query popularity and geographic access patterns.

This project demonstrates the design and implementation of a distributed search architecture featuring dynamic replication, fault tolerance, replica management, and geographically aware query routing.

---

## Features

- Dynamic replica creation based on query frequency
- Geographic-aware request routing
- gRPC-based communication between services
- Master–Replica architecture
- Backup master for fault tolerance
- Sequentially consistent metadata synchronization
- LRU-based replica eviction
- Inverted index search
- Background crawler for index updates

---

## Architecture

```
                    Client
                       │
                       ▼
                 Master Server
               /              \
      Backup Master      Replica Manager
              │                │
              ▼                ▼
      Dynamic Replica     Dynamic Replica
              │                │
              └────── Search Index ──────┘

                     ▲
                     │
                  Crawler
```

---

## Repository Structure

```
.
├── client.py
├── crawler.py
├── master.py
├── masterbackup.py
├── replica.py
├── writeservice.py
├── utils.py
├── protos/
└── data/
```

---

## Technologies

- Python
- gRPC
- Protocol Buffers
- Distributed Systems
- Inverted Indexing

---

## Running

Requires Python 3.9+ and a running MongoDB instance (see `CONTRIBUTING.md` for full setup, including seeding the metadata db).

```bash
pip install -r requirements.txt
```

Generate the gRPC/protobuf bindings (not checked into this repo - built from `protos/search.proto`):

```bash
bash generate_proto.sh
```

Start the master

```bash
python master.py
```

Start backup

```bash
python masterbackup.py
```

Start replica

```bash
python replica.py
```

Run crawler

```bash
python crawler.py
```

Run client

```bash
python client.py
```

---

## Future Improvements

- Docker support
- Kubernetes deployment
- Redis caching
- PostgreSQL metadata store
- Prometheus monitoring
- Leader election using Raft
- Smarter replica placement
- Distributed indexing

---