'''
Utility functions
'''

from pymongo import InsertOne, DeleteOne, ReplaceOne, UpdateOne
from pymongo.errors import BulkWriteError
from bson import BSON
from bson import json_util
from argparse import ArgumentParser
import argparse
import logging
import pprint
import json
import sys
from pymongo import MongoClient
from config import config

# Global MongoDB Client with connection pooling
mongo_client = MongoClient(config.MONGO_URI, maxPoolSize=100)


# TODO : add time of creation/update
# Metadata db

def add_to_metadatadb(sender, replica_ip, location, indices, verbose=True):
    record = {}
    record["replica_ip"] = replica_ip
    record["location"] = location
    record["indices"] = indices

    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    metadata_coll = db.metadata
    # unique index

    metadata_coll.create_index("location", unique=True)

    try:
        metadata_coll.update_one({"location": location}, {"$set": {
                                 "location": location,  "replica_ip": replica_ip, "indices": list(indices)}}, upsert=True)
        if (verbose):
            print("Success")
            print("Added ", str(record), " to metadata of ", sender)
    except Exception as e:
        print("Failed due to ", str(e))


def query_metadatadb_indices(sender, location):
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    entry = db.metadata.find_one({'location': location})

    words = []
    if entry is not None:
        for word in entry['indices']:
            words.append(word)
        return words


def update_replica_ip(sender, location, new_replica_ip):
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    try:
        db.metadata.update_one({"location": location}, {
                               "$set": {"replica_ip": new_replica_ip}}, upsert=True)
    except Exception as e:
        print("Failed due to ", str(e))


def get_replica_ips_locs_from_metadatadb(sender):
    client = mongo_client
    try:
        if sender == 'master':
            db = client.masterdb
        elif sender == 'backup':
            db = client.backupdb
        else:
            db = client[sender+"db"]

        responses = db.metadata.find(
            {}, {'replica_ip': 1, 'location': 1, '_id': 0})
        # NOTE: must consume cursor BEFORE closing the client — pymongo cursors are
        # lazy, and closing the client invalidates the cursor.
        result = []
        for response in responses:
            result.append((response["replica_ip"], response["location"]))
        return result
    finally:
        pass


def query_metadatadb(sender, location, search_terms):
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    metadata_coll = db.metadata
    replica = metadata_coll.find_one({"location": location})
    if replica is None:
        return None, False

    status = True
    for search_term in search_terms:
        if search_term not in list(replica["indices"]):
            status = False
            break

    return replica["replica_ip"], status


def get_similar(sender, words):
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    indices = db.indices
    responses = indices.find({"status": "committed", "name": {"$in": words}})

    similar = set()
    if responses is not None:
        for response in responses:
            similar.update(response["sim_words"])

    return list(similar)


def get_data_for_indices(sender, indices):
    indices = get_similar(sender, indices)

    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    indices_coll = db.indices
    # print indices, len(indices)
    responses = indices_coll.find(
        {"status": "committed", "name": {"$in": indices}})
    # print "Works till here"
    result = json_util.dumps(responses)
    # print "Here too"
    return result, indices


def querydb(sender, search_term):
    '''Query on mongodb database for suitable response for search term
    '''
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    print("Searching ", sender)
    indices = db.indices
    response = indices.find_one({"status": "committed", "name": search_term})
    if response is not None:
        return response["urls"]
    return []


def getallwords(sender):
    '''Query on mongodb database for all name words
    '''
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    indices = db.indices
    responses = indices.find({}, {'name': 1, '_id': 0})

    words = []
    if responses is not None:
        for response in responses:
            words.append(response['name'])

    return words


def addtodb(sender, data):
    '''Add json string to db
    '''
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    print("Adding to DB")
    if type(data) != type(list()):
        # NOTE (py3 port): the old `.decode('string-escape').strip('"')` relied on a
        # byte-string codec that Python 3 removed entirely (str has no .decode() at all).
        # Tracing the caller (writeservice.WriteIndicesToTable does json.dumps(request.data),
        # and request.data already came in as crawler.py's json.dumps(self.data)) shows this
        # value is JSON-encoded TWICE, so it needs to be decoded twice too.
        data = json.loads(json.loads(data))
    indices = db.indices

    requests = []
    for rec in data:
        # print rec
        requests.append(UpdateOne({"name": rec["name"]}, {"$set": {
                        "status": "committed", "name": rec["name"], "urls": rec["urls"], "sim_words": rec["sim_words"], "is_new": 1}}, upsert=True))

    if len(requests) == 0:
        return True

    try:
        result = indices.bulk_write(requests, ordered=False)
    except BulkWriteError as exc:
        print("Error: ", exc.details)

    # NOTE (py3 port): Collection.count() was removed in pymongo 4.0 (deprecated since 3.7)
    print("Records: ", indices.count_documents({}))
    return True


def removefromdb(sender, data):
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    indices = db.indices
    # NOTE (py3 port): Collection.remove() was removed in pymongo 4.0; delete_many() is the replacement
    indices.delete_many({'name': {'$in': data}})

    return True


def commitdb(sender):
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    print("COMMIT")
    indices = db.indices

    # remove duplicate records whose status is committed and who have names in the pending list
    words = indices.find({"status": "pending"}, {"name": 1, '_id': 0})
    words = [x['name'] for x in words]
    print("Duplicates : ", words)
    # NOTE (py3 port): remove()/update(multi=True) were removed in pymongo 4.0;
    # delete_many()/update_many() are the direct replacements.
    status = indices.delete_many(
        {"status": "committed", "name": {"$in": words}})
    print(status)

    # update pending records to committed
    status = indices.update_many({'status': 'pending'},
                                 {'$set': {'status': 'committed'}})
    print("Write status ", status)
    print("Total length of documents ", indices.count_documents({}))


def rollbackdb(sender):
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    print("ROLLBACK")
    indices = db.indices
    status = indices.delete_many({'status': 'pending'})
    print(status)


def init_logger(db_name, logging_level):
    logger = logging.getLogger(db_name)
    logger.setLevel(logging_level)
    # add handlers only if not already added
    if not len(logger.handlers):
        # create a logging format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Stream handler for stdout (12-Factor App / container log aggregator compatibility)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging_level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # Rotating file handler to prevent disk exhaustion (10MB max, 5 backups)
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(
            'log' + db_name + '.log',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        fh.setLevel(logging_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger


def parse_level(level):
    if level == 'DEBUG':
        logging_level = logging.DEBUG
    elif level == 'INFO':
        logging_level = logging.INFO
    elif level == 'WARNING':
        logging_level = logging.WARNING
    elif level == 'ERROR':
        logging_level = logging.ERROR
    elif level == 'CRITICAL':
        logging_level = logging.CRITICAL
    else:
        message = 'Invalid choice! Please choose from DEBUG, INFO, WARNING, ERROR, CRITICAL'
        # NOTE (py3 port, pre-existing bug, not py2/3-related): this referenced an undefined
        # `self` (parse_level is a plain function, not a method) and never actually raised
        # the exception it built - so an invalid level would silently fall through to
        # `return logging_level` with logging_level unset -> UnboundLocalError. argparse's
        # own `choices=` already prevents this branch from being hit in practice, but it's
        # a live landmine, so it's a real raise now.
        raise ValueError(message)
    return logging_level


import os
_cached_replica_ips = None
_replica_file_mtime = 0

def read_replica_filelist():
    global _cached_replica_ips, _replica_file_mtime
    file_path = config.REPLICAS_LIST_FILE
    try:
        mtime = os.stat(file_path).st_mtime
    except FileNotFoundError:
        return _cached_replica_ips or {}
        
    if _cached_replica_ips is not None and mtime == _replica_file_mtime:
        return _cached_replica_ips

    replica_ips = {}
    with open(file_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue  # skip blank or malformed lines
            # IP LOCATION
            ip = parts[0].strip()
            location = parts[1].strip()
            if location not in replica_ips:
                replica_ips[location] = []
            replica_ips[location].append(ip)
            
    _cached_replica_ips = replica_ips
    _replica_file_mtime = mtime
    return replica_ips


def get_all_replica_ips(sender):
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    entry = db.metadata.find({})

    replica_ips = []

    if entry is not None:
        for replica in entry:
            # print replica
            replica_ips.append(replica["replica_ip"])
        return replica_ips


def get_data_for_replica(sender, replica_ip):
    # return get_data_for_indices('master', ["freakish"])

    # location, replica_ip, indices
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    else:
        db = client.backupdb

    metadata_coll = db.metadata
    indices_coll = db.indices
    replica = metadata_coll.find_one({"replica_ip": replica_ip})

    indices = replica["indices"]

    # for indice
    # print indices, len(indices)
    responses = indices_coll.find({"is_new": 1, "name": {"$in": indices}})
    result_cur = [response for response in responses]
    indices = [result["name"] for result in result_cur]
    result = json_util.dumps(result_cur)
    return result, indices


def get_data_for_backup(sender):
    # return get_data_for_indices('master', ["freakish"])

    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    else:
        db = client.backupdb
    indices_coll = db.indices
    indices = []

    responses = indices_coll.find({"is_new": 1})
    # print responses, responses.count()
    result_cur = [response for response in responses]
    indices = [result["name"] for result in result_cur]
    result = json_util.dumps(result_cur)
    return result, indices


def updateMasterIndices(sender, data):
    client = mongo_client
    try:
        if sender == 'master':
            db = client.masterdb
        elif sender == 'backup':
            db = client.backupdb
        else:
            db = client[sender+"db"]

        # NOTE (py3 port fix): the original `type(data) != type(list(data))` would crash
        # if data is a string, because list("abc") produces ['a','b','c'] — a valid list,
        # so the check would never trigger *and* it would also fail on non-iterable types.
        # The intent is simply "if data is not already a list, deserialize it".
        if not isinstance(data, list):
            # This value comes from get_data_for_backup(), which encodes with a single
            # bson.json_util.dumps(...) call — so it needs exactly one matching
            # json_util.loads() to come back correctly.
            data = json_util.loads(data)
        indices_coll = db.indices

        requests = []
        for rec in data:
            requests.append(UpdateOne({"name": rec["name"]}, {"$set": {
                            "status": "committed", "name": rec["name"], "urls": rec["urls"], "sim_words": rec["sim_words"], "is_new": 0}}, upsert=True))

        if len(requests) == 0:
            return True

        try:
            result = indices_coll.bulk_write(requests, ordered=False)
        except BulkWriteError as exc:
            print("Error: ", exc.details)
            return False

        return True
    finally:
        pass


def update_db(sender, data):
    # print len(data), " indices updated"
    # return True
    client = mongo_client
    if sender == 'master':
        db = client.masterdb
    elif sender == 'backup':
        db = client.backupdb
    else:
        db = client[sender+"db"]

    if type(data) != type(list()):
        # NOTE (py3 port): comes from get_data_for_replica(), single bson.json_util.dumps(...)
        # upstream, so a single matching json_util.loads() is correct here (see same note
        # in updateMasterIndices above).
        data = json_util.loads(data)

    if len(data) == 0:
        print("Empty!")
        return True

    indices_coll = db.indices
    requests = []
    for rec in data:
        print(rec)
        requests.append(UpdateOne({"name": rec["name"]}, {"$set": {
                        "status": "committed", "name": rec["name"], "urls": rec["urls"], "sim_words": rec["sim_words"], "is_new": 0}}, upsert=True))

    try:
        if not len(requests) == 0:
            result = indices_coll.bulk_write(requests, ordered=False)
    except BulkWriteError as exc:
        print("Error: ", exc.details)
        return False

    # print "Records: ", indices_coll.count()
        return True

# result, indices = get_data_for_backup('master')
# result, indices = get_data_for_replica('master', 'localhost:50053')
# print result, indices
