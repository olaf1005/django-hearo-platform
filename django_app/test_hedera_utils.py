"""TODO: this is not complete and should not be run in any CI env

It requires requires us to maintain mock responses from the hts.

At the moment, it would require we enable settings.ENABLE_HTS
in settings/test.py

"""
import logging
import requests

from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth.models import User

import hedera_utils


logger = logging.getLogger(__name__)


class HederaUtilsTestCase(TestCase):
    def _create_user(self, email, password):
        data = dict(
            account_type="artist",
            dj="f",
            email=email,
            engineer="t",
            genre="",
            instruments="",
            is_musician="",
            join_band="",
            name=email,
            password=password,
            producer="f",
            teacher="f",
            write_music="f",
            city="Nairobi",
        )
        response = self.client.post("/register-ajax/", data)

        self.assertEqual(response.status_code, 200)

        user = User.objects.get(email=email)
        user.verified = True
        user.save()
        self.user = user

        return user

    def setUp(self):
        self.client = Client()
        self.user = self._create_user("test@user.com", "password")
        self._create_wallet_for_user()

    def _create_wallet_for_user(self):
        data = {"accountId": self.user.wallet.hedera_account_id}
        params = {}
        res = requests.get(
            "{}/{}".format(settings.H_HTS_API_URL, "hbarBalance"), params=params
        )
        self.assertEqual(res.json(), 0)

    def test_transfer_starter_tokens(self):
        hedera_utils.transfer_starter_tokens(self.user)
        data = {"tokenOwnerSolidityAddress": self.user.wallet.solidity_address}
        res = requests.post(
            "{}/{}".format(settings.H_HTS_API_URL, "erc20/balanceOf"), json=data
        ).json()
        self.assertEqual(res.json(), settings.NEW_USER_TOKENS)
