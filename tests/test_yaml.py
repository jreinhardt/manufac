import unittest
from manuallabour.cl import yaml_reader

class TestYAML(unittest.TestCase):
    def test_init(self):
        g = yaml_reader.graph_from_YAML('tests/yaml/simple.yaml')
        g.to_svg('test.svg')

if __name__ == '__main__':
    unittest.main()
