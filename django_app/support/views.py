import datetime
import logging

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_protect
from django.conf import settings

import openpgp_utils

from inmemoryzip import InMemoryZip


logger = logging.getLogger(__name__)


@csrf_protect
def regenerate_encryption_keys(request):
    """Regenerate the keys for the specified administrative user.

    Used if you want to rotate keys.

    This is a destructive process so should only be used if the administrative
    user doesn't have much JAM and needs to be update the keys used for example
    in encrypting user keys to support the retrieval of user keys.

    Otherwise you should be able to download your keys via the wallet page
    by providing a password.

    """
    if settings.ENABLE_HTS:
        user = request.user
        if user.is_staff and user.is_active:
            password = request.GET["password"]

            # user has wallet so we regenerate the openpgp key and reencyprt
            full_name = "{} {}".format(user.first_name, user.last_name)
            email = user.email
            key = openpgp_utils.create_key(full_name, email)
            openpgp_utils.lock(key, password)

            # create archive
            key_zip = InMemoryZip()
            key_zip.append(
                "{}_{}.asc".format(request.user.email, datetime.date.today()), str(key)
            )
            key_zip.append(
                "{}_{}_pub.asc".format(request.user.email, datetime.date.today()),
                str(key.pubkey),
            )

            response = HttpResponse(key_zip.read(), content_type="application/tar")
            response[
                "Content-Disposition"
            ] = "attachment;filename={}_{}_keys.zip".format(
                request.user.email, datetime.date.today()
            )
            return response
        return HttpResponseBadRequest()
    return HttpResponseBadRequest("Hedera spring api is not enabled")


def download_openpgp_public_key(request):
    if request.user.is_staff and request.user.is_active:
        key = openpgp_utils.load(request.user.wallet.openpgp_key)
        response = HttpResponse(key.pubkey, content_type="application/pgp-keys")
        response["Content-Disposition"] = "attachment;filename={}_{}_pub.asc".format(
            request.user.email, datetime.date.today()
        )
        return response
    return HttpResponseBadRequest()


def download_openpgp_private_key(request):
    user = request.user
    # For now we only enable this for staff users
    if user.is_staff and user.is_active:
        wallet = user.wallet
        key = openpgp_utils.load(wallet.openpgp_key)

        # create archive
        key_zip = InMemoryZip()
        key_zip.append(
            "{}_{}.asc".format(request.user.email, datetime.date.today()),
            str(wallet.openpgp_key),
        )
        key_zip.append(
            "{}_{}_pub.asc".format(request.user.email, datetime.date.today()),
            str(key.pubkey),
        )
        key_zip.append(
            "{}_{}_hedera_private_key.msg".format(
                request.user.email, datetime.date.today()
            ),
            str(wallet.hedera_private_key),
        )
        key_zip.append(
            "{}_{}_hedera_public_key.txt".format(
                request.user.email, datetime.date.today()
            ),
            str(wallet.hedera_public_key),
        )
        key_zip.append(
            "{}_{}_hedera_account_id.txt".format(
                request.user.email, datetime.date.today()
            ),
            str(wallet.hedera_account_id),
        )

        response = HttpResponse(key_zip.read(), content_type="application/tar")
        response["Content-Disposition"] = "attachment;filename={}_{}_keys.zip".format(
            request.user.email, datetime.date.today()
        )
        return response
    return HttpResponseBadRequest()
