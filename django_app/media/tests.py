"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from media.models import Song


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

    def test_song_get_formatted_length(self):
        "Test that Song.get_formatted_length returns the correct value"
        song = Song(length=147)
        self.assertEqual("0:02:27", song.get_formatted_length())
