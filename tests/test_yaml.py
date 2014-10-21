import unittest
from manuallabour.cl.yaml_reader import *

class TestYAML(unittest.TestCase):
    def test_init(self):
        g = graph_from_YAML('tests/yaml/simple.yaml')
        g.to_svg('test.svg')

class TestTime(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_time("4d").total_seconds(),345600)
        self.assertEqual(parse_time("1 hour").total_seconds(),3600)
        self.assertEqual(parse_time("3m").total_seconds(),180)
        self.assertEqual(parse_time("2s").total_seconds(),2)
        self.assertEqual(parse_time("3m2s").total_seconds(),182)
        self.assertEqual(parse_time("1h3m2s").total_seconds(),3782)
        self.assertEqual(parse_time("4d 1 hour 3m 2s").total_seconds(),349382)
        self.assertEqual(parse_time("1 day 1 hour 1 minute 1 second").total_seconds(),90061)
        self.assertEqual(parse_time("2 days 2 hours 2 minutes 2 seconds").total_seconds(),180122)
        self.assertEqual(parse_time("2 d 2 h 2 m 2 s").total_seconds(),180122)
        self.assertEqual(parse_time("2 d 2 h 2 min 2 s").total_seconds(),180122)
        self.assertEqual(parse_time(None),None)
    def test_format(self):
        t = timedelta(days=3, hours=2, minutes=1, seconds = 7)
        self.assertEqual(t,parse_time(format_time(t)))

        self.assertEqual(format_time(None),None)


if __name__ == '__main__':
    unittest.main()
