import hashlib

MAX_BITS = 10
MAX_NODES = 2 ** MAX_BITS


def getHash(key):
    result = hashlib.sha1(key.encode())
    return int(result.hexdigest(), 16) % MAX_NODES
