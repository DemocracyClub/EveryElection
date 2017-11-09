# -*- coding: utf-8 -*-

from unittest import TestCase
from uk_election_ids.slugger import slugify

class TestSlugify(TestCase):

    """
    For this particular use-case, we are primarily concerned with
    1. Slugging characters that appear in names of places in the UK sensibly
    2. Validating that slugging is an idempotent operation
    """

    def test_st_helens(self):
        self.assertEqual(slugify("St. Helen's"), 'st-helens')
        self.assertEqual(slugify(slugify("St. Helen's")), 'st-helens')

    def test_westward_ho(self):
        self.assertEqual(slugify("Westward Ho!"), 'westward-ho')
        # (yes it actually does have an exclamation mark in the name)
        # https://en.wikipedia.org/wiki/Westward_Ho!
        self.assertEqual(slugify(slugify("Westward Ho!")), 'westward-ho')

    def test_ynys_mon(self):
        self.assertEqual(slugify("Ynys Môn"), 'ynys-mon')
        self.assertEqual(slugify(slugify("Ynys Môn")), 'ynys-mon')

    def test_eilean_a_cheo(self):
        self.assertEqual(slugify("Eilean a' Cheò"), 'eilean-a-cheo')
        self.assertEqual(slugify(slugify("Eilean a' Cheò")), 'eilean-a-cheo')

    def test_leading_trailing_whitespace(self):
        self.assertEqual(slugify("   foo \t "), 'foo')
        self.assertEqual(slugify(slugify("   foo \t ")), 'foo')
