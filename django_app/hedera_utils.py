import logging
import itertools
import hashlib

import pgpy
import requests

from django.conf import settings
from django.utils import timezone

from accounts.models import HTSTokenTransfer, Wallet, WalletRecovery, User
from media.models import Listen
from media.views import (
    create_token_transfers_for_listen,
    get_value_and_facilitation_fee,
)

import openpgp_utils


logger = logging.getLogger(__name__)


class GetUserPrivateKeyError(Exception):
    pass


class CheckTokenBalanceError(Exception):
    pass


class KeyUnlockError(Exception):
    pass


class HederaAccountCreationError(Exception):
    pass


class HederaAccountSetupError(Exception):
    pass


class StarterTokensTransferError(Exception):
    pass


class ProcessUnpaidListens(Exception):
    pass


def pay_unpaid_listens(request, private_key):
    # process any unprocessed token transfers
    unpaid_listens = Listen.objects.filter(user=request.user, datetime_processed=None)
    if unpaid_listens:
        logger.info("processing {} unprocessed listens".format(unpaid_listens.count()))
    for listen in unpaid_listens:
        try:
            seconds_to_pay = listen.seconds
            song = listen.song
            # success will be set in transfer token
            data = create_token_transfers_for_listen(request.user, song, seconds_to_pay)

            if data:
                value, facilitation_fee = get_value_and_facilitation_fee(seconds_to_pay)
                tokentransfer = HTSTokenTransfer(
                    listen=listen,
                    from_user=request.user,
                    for_song=song,
                    value=value,
                    facilitation_fee=facilitation_fee,
                    data=data,
                )
                tokentransfer.save()
                tokentransfer.transfer_token(private_key)
                listen.datetime_processed = timezone.now()
                listen.save()
        except Exception as e:
            raise ProcessUnpaidListens(e)


def create_token_transfer_json_data(from_account, from_private_key, to_accounts):
    data = {
        "fromAccount": {"accountId": from_account, "privateKey": from_private_key},
        "toAccounts": [],
    }
    for account_id, amount in to_accounts:
        data["toAccounts"].append({"accountId": account_id, "amount": amount})
    return data


def remove_private_keys_from_transaction(transfer):
    transfer_data = transfer.data.copy()
    for key, _ in enumerate(transfer_data):
        if "privateKey" in transfer_data[key]["fromAccount"]:
            del transfer_data[key]["fromAccount"]["privateKey"]
    return transfer_data


def create_or_update_hedera_account(request, password, private_key):
    user = request.user
    if settings.ENABLE_HTS:
        # if the user does not have a hedera wallet,
        # redirect them to the dashboard wallet in which the
        # new account will be displayed
        try:
            wallet = user.wallet
            # Update token balance on network
            if not wallet.account_associated_with_token:
                try:
                    associate_account_with_wallet(user, private_key)
                except HederaAccountSetupError as e:
                    logger.error(e, exc_info=True)
            try:
                balance = check_token_balance_on_hedera_network(user)
                wallet.token_balance = balance
                wallet.token_balance_last_update = timezone.now()
                wallet.save()
            except CheckTokenBalanceError as e:
                # log the previous error the account was already associated
                # with the token
                logger.error(e, exc_info=True)

            if not settings.DISABLE_STARTER_TOKENS:
                # Transfer starter tokens
                try:
                    if not wallet.received_starter_tokens:
                        transfer_starter_tokens(user)
                except StarterTokensTransferError as e:
                    logger.error(e, exc_info=True)

            try:
                pay_unpaid_listens(request, private_key)
            except ProcessUnpaidListens as e:
                logger.error(e, exc_info=True)
        except User.wallet.RelatedObjectDoesNotExist:  # type: ignore
            # Create wallet
            try:
                wallet = create_wallet(user, password)

                if not private_key:
                    private_key = get_user_private_key(user, password)

                # Need to set private session key here
                request.session[settings.PRIVATE_KEY_SESSION_KEY] = private_key

                # associate wallet with token
                try:
                    associate_account_with_wallet(user, private_key)
                except HederaAccountSetupError as e:
                    logger.error(e, exc_info=True)
            except (HederaAccountCreationError, GetUserPrivateKeyError) as e:
                logger.error(e, exc_info=True)
            else:
                if not settings.DISABLE_STARTER_TOKENS:
                    # Transfer starter tokens
                    try:
                        if not wallet.received_starter_tokens:
                            transfer_starter_tokens(user)
                    except StarterTokensTransferError as e:
                        logger.error(e, exc_info=True)


def get_user_private_key(user, password):
    private_key = None
    try:
        encrypted_message = pgpy.PGPMessage.from_blob(user.wallet.hedera_private_key)
        key = pgpy.PGPKey()
        key.parse(user.wallet.openpgp_key)

        with key.unlock(password) as unlocked_key:
            decrypted_message = unlocked_key.decrypt(encrypted_message)
            if len(decrypted_message.message) == 96:
                # We have the key
                private_key = decrypted_message.message
    except Exception as e:
        raise GetUserPrivateKeyError(e)
    else:
        return private_key


def check_token_balance_on_hedera_network(user):
    logger.info("checking token balance for {}".format(user.email))
    try:
        res = requests.get(
            "{}/token/balance/{}".format(
                settings.H_HTS_API_URL, user.wallet.hedera_account_id
            )
        )
        if res.ok:
            return int(res.json())
        else:
            raise CheckTokenBalanceError(
                "ERROR {}: {}".format(res.status_code, res.json())
            )
    except Exception as e:
        raise CheckTokenBalanceError(e)


def send_tokens(user):
    logger.info("transfering starter tokens")
    num_trial_tokens = settings.NEW_USER_TOKENS
    wallet = user.wallet
    try:
        data = dict(
            toAccounts=[
                {"accountId": user.wallet.hedera_account_id, "amount": num_trial_tokens}
            ]
        )
        res = requests.post(
            "{}/token/transfer".format(settings.H_HTS_API_URL), json=data
        )
        if res.ok:
            # get token balance from the network
            wallet.token_balance = check_token_balance_on_hedera_network(user)
            wallet.token_balance_last_update = timezone.now()
            wallet.received_starter_tokens = True
            wallet.save()
        else:
            raise StarterTokensTransferError(
                "ERROR {}: {}".format(res.status_code, res.json())
            )
    except Exception as e:
        raise StarterTokensTransferError(e)


def transfer_starter_tokens(user):
    logger.info("transfering starter tokens")
    num_trial_tokens = settings.NEW_USER_TOKENS
    wallet = user.wallet
    try:
        data = dict(
            toAccounts=[
                {"accountId": user.wallet.hedera_account_id, "amount": num_trial_tokens}
            ]
        )
        res = requests.post(
            "{}/token/transfer".format(settings.H_HTS_API_URL), json=data
        )
        if res.ok:
            # get token balance from the network
            wallet.token_balance = check_token_balance_on_hedera_network(user)
            wallet.token_balance_last_update = timezone.now()
            wallet.received_starter_tokens = True
            wallet.save()
        else:
            raise StarterTokensTransferError(
                "ERROR {}: {}".format(res.status_code, res.json())
            )
    except Exception as e:
        raise StarterTokensTransferError(e)


def _create_recovery_keys(user, private_key):
    logger.info("creating recovery keys")
    # Create the recovery keys
    for permutation in list(
        itertools.permutations(
            settings.RECOVERY_OPENPGP_PUBLIC_KEYS,
            r=settings.NUM_AUTHORIZERS_REQUIRED_FOR_PASSWORD_RESET,
        )
    ):
        recovery_key_hashes = []
        message = private_key
        for (email, pgpkey) in permutation:
            key = pgpy.PGPKey()
            key.parse(pgpkey)
            message = pgpy.PGPMessage.new(str(message))
            message = key.encrypt(message)
            md5hash = hashlib.md5()
            md5hash.update(str(pgpkey).strip().encode("utf-8"))
            recovery_key_hashes.append(md5hash.hexdigest())
        WalletRecovery.objects.create(
            wallet=user.wallet,
            encrypted_key=str(message),
            recovery_key_hashes=recovery_key_hashes,
        )
    logger.info("Creating recovery wallets for %s", user.email)


def create_wallet(user, password):
    logger.info("creating wallet")
    full_name = "{} {}".format(user.first_name, user.last_name)

    email = user.email

    # Create openpgp key and lock it using the user password
    key = openpgp_utils.create_key(full_name, email)
    openpgp_utils.lock(key, password)

    # Create the Hedera account
    try:
        res = requests.post("{}/account/create".format(settings.H_HTS_API_URL))
        if settings.DEBUG:
            logger.debug(res)
            logger.debug(res.json())
        if res.ok:
            res = res.json()
        else:
            raise HederaAccountCreationError(
                "ERROR {}: {}".format(res.status_code, res.json())
            )
    except Exception as e:
        logger.error("AN ERROR OCCURRED CREATED THE HEDERA WALLET ACCOUNT!")
        raise HederaAccountCreationError(e)
    else:
        account_id = res["accountId"]
        public_key = res["publicKey"]
        private_key = res["privateKey"]

        # Create message and encrypt
        message = pgpy.PGPMessage.new(private_key)
        encrypted_private_key = str(key.pubkey.encrypt(message))

        wallet = Wallet.objects.create(
            user=user,
            openpgp_key=str(key),
            hedera_account_id=account_id,
            hedera_private_key=encrypted_private_key,
            hedera_public_key=public_key,
        )
        _create_recovery_keys(user, private_key)
        return wallet


def associate_account_with_wallet(user, private_key):
    logger.info("associating account with token")
    try:
        data = dict(accountId=user.wallet.hedera_account_id, privateKey=private_key)
        res = requests.post(
            "{}/account/setup".format(settings.H_HTS_API_URL), json=data
        )
        if settings.DEBUG:
            logger.debug(res)
            logger.debug(res.json())

        if res.ok:
            res = res.json()
        else:
            raise HederaAccountSetupError(
                "ERROR {}: {}".format(res.status_code, res.json())
            )
        wallet = user.wallet

        # needs to be set so we don't try to transfer tokens to an account not yet
        # associated with the token
        wallet.account_associated_with_token = True
        wallet.save()
    except Exception as e:
        logger.error("AN ERROR OCCURRED ASSOCIATING THE TOKEN TO THE WALLET!")
        raise HederaAccountSetupError(e)
