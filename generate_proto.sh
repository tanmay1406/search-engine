#!/usr/bin/env bash
# Generates search_pb2.py and search_pb2_grpc.py from protos/search.proto.
#
# These two generated files were NOT present anywhere in the original repo
# (confirmed: no *_pb2* file exists in the zip, and protos/ contains only the
# .proto source) even though master.py, replica.py, client.py, etc. all
# `import search_pb2` / `import search_pb2_grpc` directly. Nobody could run
# this project without running this generation step first - it just wasn't
# documented as part of "Running the code" in the README (it IS mentioned,
# correctly, in CONTRIBUTING.md - that's where this command comes from).
#
# Run this once, from the repo root, after `pip install -r requirements.txt`:
set -e

python -m grpc_tools.protoc \
    -I./protos \
    --python_out=. \
    --grpc_python_out=. \
    protos/search.proto

echo "Generated search_pb2.py and search_pb2_grpc.py in $(pwd)"
