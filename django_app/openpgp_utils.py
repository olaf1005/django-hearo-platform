import pgpy
from pgpy.constants import (
    PubKeyAlgorithm,
    KeyFlags,
    HashAlgorithm,
    SymmetricKeyAlgorithm,
    CompressionAlgorithm,
)


def create_key(full_name, email):
    # We can start by generating a primary key. For this example, we'll use RSA, but it could be DSA or ECDSA as well
    key = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)

    # We now have some key material, but our new key doesn't have a user ID yet, and therefore is not yet usable!
    uid = pgpy.PGPUID.new(full_name, comment="tune.fm key", email=email)

    # Now we must add the new user id to the key. We'll need to specify all of our preferences at this point
    # because PGPy doesn't have any built-in key preference defaults at this time
    # this example is similar to GnuPG 2.1.x defaults, with no expiration or preferred keyserver
    key.add_uid(
        uid,
        usage={KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage},
        hashes=[
            HashAlgorithm.SHA256,
            HashAlgorithm.SHA384,
            HashAlgorithm.SHA512,
            HashAlgorithm.SHA224,
        ],
        ciphers=[
            SymmetricKeyAlgorithm.AES256,
            SymmetricKeyAlgorithm.AES192,
            SymmetricKeyAlgorithm.AES128,
        ],
        compression=[
            CompressionAlgorithm.ZLIB,
            CompressionAlgorithm.BZ2,
            CompressionAlgorithm.ZIP,
            CompressionAlgorithm.Uncompressed,
        ],
    )

    return key


def lock(key, password):
    # Protect key with pass takes the key and encrypts it with the user pass
    # this should be stored for the user only, since if we want to unlock a users keys
    # we wont have the passphrase anyway
    # No return type
    key.protect(password, SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)


def export(key):
    # Export keys in binary format
    # In python 3, use bytes(key)
    return key.__bytes__()


def load(blob):
    # Loads a key from a blob
    key, _ = pgpy.PGPKey.from_blob(blob)
    return key
