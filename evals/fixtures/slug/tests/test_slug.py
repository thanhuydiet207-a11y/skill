import unittest
from slugs.slug import slugify


class Slugify(unittest.TestCase):
    def test_spaces_become_dashes(self):self.assertEqual(slugify('Hello World'),'hello-world')
    def test_case_is_lowered(self):self.assertEqual(slugify('ABC'),'abc')
