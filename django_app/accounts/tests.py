import os
import unittest

from django.urls import reverse

from django.test import TestCase, Client

from .models import Location, User, HTSTokenTransfer
from media.models import Song, Listen


# class TestProfileSave(TestCase):
#     fixtures = ["one_musician"]

#     def setUp(self):
#         self.client = Client()
#         self.client.login(email="musician@example.com", password="test")

#     def test_survives_duplicate_cities(self):
#         payload = {
#             "biography": "Foo",
#             "city": "Houston, TX, USA",
#             "dj": "f",
#             "engineer": "f",
#             "experience": "bar",
#             "genre": "electro",
#             "goals": "foo",
#             "influences": "bar",
#             "instruments": "keyboard",
#             "is_musician": "t",
#             "join_band": "f",
#             "new_people": "f",
#             "producer": "f",
#             "start_band": "f",
#             "teacher": "f",
#             "write_music": "f",
#             "account_type": "artist",
#         }

#         self.assertEqual(Location.objects.filter(pk=1).count(), 1)
#         Location.objects.create(
#             lng=-95.36938959999999, lat=29.7601927, most_exact="Houston, TX, USA"
#         )

#         res = self.client.post(reverse("accounts_account_profile_ajax"), payload)
#         self.assertEqual(res.status_code, 200)

#     def test_get(self):
#         res = self.client.get(reverse("accounts_account_profile_ajax"))
#         self.assertEqual(res.status_code, 400)


class TestIndexPage(TestCase):
    def setUp(self):
        self.client = Client()

    def test_unauthenticated_account_index(self):
        """
        Attemp to access account index page unauthenticated
        """
        response = self.client.get("/my-account/index/")
        self.assertRedirects(response, "/signup/?next=/my-account/index/")

    def test_authenticated_account_index(self):
        """
        Create a user and attempt to access account index page as an authenticated user
        """

        email = "test@test.com"
        password = "password"
        payload = {
            "biography": "Foo",
            "city": "Houston, TX, USA",
            "dj": "f",
            "engineer": "f",
            "experience": "bar",
            "genre": "electro",
            "goals": "foo",
            "influences": "bar",
            "instruments": "keyboard",
            "is_musician": "t",
            "join_band": "f",
            "new_people": "f",
            "producer": "f",
            "start_band": "f",
            "teacher": "f",
            "write_music": "f",
            "account_type": "artist",
            "email": email,
            "password": password,
            "name": "test user",
        }
        self.client.post(reverse("accounts_register_ajax"), payload)

        self.client.login(email=email, password=password)

        res = self.client.get("/my-account/index/")

        self.assertEqual(res.status_code, 200)


class BaseTestTransfer(TestCase):
    def _create_user(self, first_name, last_name, email, **kwargs):
        payload = {
            "biography": "Foo",
            "city": "Houston, TX, USA",
            "dj": "f",
            "engineer": "f",
            "experience": "bar",
            "genre": "electro",
            "goals": "foo",
            "influences": "bar",
            "instruments": "keyboard",
            "is_musician": "t",
            "join_band": "f",
            "new_people": "f",
            "producer": "f",
            "start_band": "f",
            "teacher": "f",
            "write_music": "f",
            "account_type": "artist",
            "email": email,
            "password": "password",
            "name": "{} {}".format(first_name, last_name),
        }
        payload.update(kwargs)
        res = self.client.post(reverse("accounts_register_ajax"), payload)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(User.objects.filter(email=email).count(), 1)

        user = User.objects.get(email=email)

        return user

    def _create_page(self, user):
        payload = dict(
            account_type="band",
            name="{} {}".format(user.first_name, user.last_name),
            is_musician="0",
            instruments="guitar",
            join_band="f",
            write_music="f",
            teacher="f",
            dj="f",
            producer="f",
            engineer="f",
            city="Houston",
            genre="various",
        )
        self.client.post(reverse("accounts_create_page_ajax"), payload)

    def setUp(self):
        self.client = Client()


class TestTransferWalletDoesNotExist(BaseTestTransfer):
    """Users without wallets will not have a solidity address.
    Test that users without a wallet (Solidity address) are
    filtered out"""

    @unittest.skipIf(bool(os.getenv("CI_BUILD_REF_NAME")), reason="Requires hts")
    def test_invalid_solidity_addresses_are_filtered(self):
        self.user = self._create_user("Test", "Artist", "test@artist.com")
        self.client.login(email=self.user.email, password="password")
        self._create_page(self.user)

        self.user_2 = self._create_user("Test", "Artist 2", "test2@artist.com")
        self.client.login(email=self.user_2.email, password="password")
        self.page_2 = self._create_page(self.user_2)

        import ipdb

        ipdb.set_trace()
        self.user_2.wallet.delete()

        for num in range(10):
            # User 1 songs
            song = Song(
                online=True,
                title="Test song {}".format(num),
                visible=True,
                profile=self.user.profile,
            )
            song.save()
            self.song = song

        for song in Song.objects.all():
            # User 2 listens
            listen = Listen(user=self.user_2, song=song, seconds=100,)
            listen.save()

        # # Test to ensure invalid are filtered out
        # query = Listen.objects.filter(datetime_processed=None).values("user", "song")

        self.assertEqual(HTSTokenTransfer.objects.count(), 0)
