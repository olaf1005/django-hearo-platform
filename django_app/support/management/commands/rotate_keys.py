import logging
import hashlib
import pgpy
import getpass

from django.core.management.base import BaseCommand

from accounts.models import WalletRecovery
from hedera_utils import _create_recovery_keys


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Rotate keys used to generate recovery keys"

    def add_arguments(self, parser):
        parser.add_argument(
            "key_files", nargs="+", help="Key file separated by a comma"
        ),
        parser.add_argument(
            "--count", action="store_true", help="Count the number of users affected"
        )

    def handle(self, *args, **options):
        keys = {}
        key_files = options["key_files"]
        for key_path in key_files:
            key, _ = pgpy.PGPKey.from_file(key_path)
            md5hash = hashlib.md5()
            md5hash.update(str(key.pubkey).encode("utf-8").strip())
            password = getpass.getpass(
                "Enter the password for key {}: ".format(key_path)
            )
            with key.unlock(password) as unlocked_key:
                # If the password can't unlock the password then an error will be
                # raised here
                pass
            keys[md5hash.hexdigest()] = {"key": key, "password": password}

        # Look for the keys provided for each user to determine what
        # we can reset
        recovery_key_hashes = list(keys.keys())

        if options["count"]:
            logger.info(
                "Keys affected %s",
                WalletRecovery.objects.filter(
                    recovery_key_hashes__contains=recovery_key_hashes
                ).count(),
            )
            logger.info(
                "Users affected %s",
                WalletRecovery.objects.filter(
                    recovery_key_hashes__contains=recovery_key_hashes
                )
                .distinct("wallet_id")
                .count(),
            )
        else:
            updated_wallets = set()
            for recoverywallet in WalletRecovery.objects.filter(
                recovery_key_hashes__contains=recovery_key_hashes
            ):
                message = recoverywallet.get_encrypted_key_object()
                wallet = recoverywallet.wallet
                # If we already created new recovery wallets, we can delete the remaining
                # older recovery keys
                if wallet.id in updated_wallets:
                    recoverywallet.delete()
                else:
                    recovery_key_hashes = recoverywallet.recovery_key_hashes
                    # We decrypt in reverse
                    recovery_key_hashes.reverse()
                    for key_hash in recovery_key_hashes:
                        key = keys[key_hash]
                        with key["key"].unlock(key["password"]) as unlocked_key:
                            try:
                                message = unlocked_key.decrypt(message).message
                            except (
                                pgpy.errors.PGPDecryptionError,
                                pgpy.errors.PGPError,
                            ):
                                logger.error("Could not decrypt..")
                            else:
                                # we have a decrypted message
                                if len(message) == 96:
                                    # We have the key
                                    updated_wallets.add(wallet.id)
                                    logger.info("Found key %s", message)
                                    _create_recovery_keys(wallet.user, message)
                                    break
                                else:
                                    message = pgpy.PGPMessage.from_blob(message)
