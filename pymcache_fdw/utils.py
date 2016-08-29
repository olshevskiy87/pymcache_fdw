import json

from multicorn.utils import log_to_postgres, WARNING, ERROR
from pymemcache.client.base import Client

import defaults


def _json_serializer(key, value):
    if isinstance(value, str):
        return value, 1
    elif isinstance(value, unicode):
        return value, 0
    return json.dumps(value), 2


def _json_deserializer(key, value, flags):
    if flags in [0, 1]:
        return value
    if flags == 2:
        return json.loads(value)
    raise Exception('Unknown serialization format')


def connect(options):
    # memcache host name
    host = defaults.host
    if 'host' in options:
        host = options['host']
    else:
        log_to_postgres('Using default host: %s' % host, WARNING)

    # memcache port
    port = int(defaults.port)
    if 'port' in options:
        port = int(options['port'])
    else:
        log_to_postgres('Using default port: %s' % port, WARNING)

    client = None
    try:
        client = Client(
            (host, port),
            serializer=_json_serializer,
            deserializer=_json_deserializer
        )
    except Exception as e:
        log_to_postgres('could not connect to memcache: %s' % str(e), ERROR)
    return client
