# Multi-stage Dockerfile for the Distributed Search Engine
# Builds protobuf stubs and installs dependencies in a builder stage,
# then copies only the runtime artifacts into a slim production image.

FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies for grpcio compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto definitions and generate stubs
COPY protos/ protos/
RUN python -m grpc_tools.protoc \
    -I protos/ \
    --python_out=. \
    --grpc_python_out=. \
    protos/search.proto

# --- Production stage ---
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy generated protobuf stubs from builder
COPY --from=builder /app/search_pb2.py /app/search_pb2_grpc.py ./

# Copy application source
COPY *.py ./
COPY data/ data/
COPY replicas_list.txt ./
COPY .env.example .env

# Expose default gRPC ports
EXPOSE 50051 50053 50060 50063

# Default command (overridden in docker-compose)
CMD ["python", "master.py", "--ip", "master:50051", "--backup", "backup:50063"]
