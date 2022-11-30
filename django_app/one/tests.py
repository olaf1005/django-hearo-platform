import unittest

from django.test import TestCase
from django.core.management import call_command

from state import HearoOneState


class SimpleTest(TestCase):
    fixtures = [
        "austin_musician",
        "houston_musician",
        "french_musician",
        "locations",
        "miami_musician",
    ]

    def setUp(self):
        if not getattr(self.__class__, "_haystack_ready", None):
            call_command("clear_index", interactive=False)
            call_command("update_index", interactive=False)
            self.__class__._haystack_ready = True

    def test_all(self):
        state = HearoOneState("/all/")
        results = state.results(
            {
                "offset": 0,
                "count": 20,
                "ranking": "hottest",
                "time": "week",
                "search_query": "",
                "price": "all",
            }
        )

        strings = [str(r.object) for r in results]

        expected = [
            "John Doe",
            "Now I'm a cowboy",
            "I Once A Rhinoceros!",
            "Martin Java",
            "Now I'm a cowboy",
            "Cowboy One",
            "Alligator One",
            "Alligator blues",
        ]

        self.assertEqual(strings, expected)

    @unittest.skip("something aint thread safe")
    def test_limit(self):
        state = HearoOneState("/all/")
        results = state.results(
            {
                "offset": 2,
                "count": 4,
                "ranking": "hottest",
                "time": "week",
                "search_query": None,
                "price": "all",
            }
        )

        strings = [str(r.object) for r in results]

        expected = [
            "I Once A Rhinoceros!",
            "Martin Java",
            "Now I'm a cowboy",
            "Cowboy One",
        ]

        self.assertEqual(strings, expected)
