import codecs

from protobuf_to_dict import protobuf_to_dict
from pymacaroons.serializers import BinarySerializer

from charged.lnnode.protobuf import MacaroonId


def parse_lnd_macaroon_identifier(macaroon_hex):
    """Parse the LND specific identifier from a hex encoded macaroon using protobuf

    Args:
        macaroon_hex (bytes): containing hex byte string

    Examples:

    >>> parse_lnd_macaroon_identifier(b'0201036...CF17CE17')
    {'nonce': b'dead', 'storage_id': b'0', 'ops': [{'entity': 'invoices': 'actions': ['read', 'write']}]}

    Notes:
        Use dict comprehension to extract ops dict:
        {item['entity']: item['actions'] for item in protobuf_to_dict(m_id)['ops']}

    """
    macaroon_bytes = codecs.decode(macaroon_hex, 'hex')
    macaroon = BinarySerializer().deserialize_raw(macaroon_bytes)

    m_id = MacaroonId().FromString(macaroon.identifier_bytes[1:])
    return protobuf_to_dict(m_id)


def parse_lnd_macaroon_identifier_no_pb(macaroon_hex):
    """Parse the LND specific identifier from a hex encoded macaroon without protobuf

    Args:
        macaroon_hex (bytes): containing hex byte string

    Examples:

    >>> parse_lnd_macaroon_identifier_no_pb(b'0201036...CF17CE17')
    {'invoices': ['read', 'write']}

    """
    macaroon_bytes = codecs.decode(macaroon_hex, 'hex')
    macaroon = BinarySerializer().deserialize_raw(macaroon_bytes)

    ret = dict()
    for item in macaroon.identifier.split(b'\x1a')[1:]:
        elements = item.split(b'\n')[1].split(b'\x12')

        key = elements[0][1:].decode()
        values = list()
        for value in elements[1:]:
            v = value[1:].decode()
            values.append(v)

        ret.update({key: values})

    return ret
