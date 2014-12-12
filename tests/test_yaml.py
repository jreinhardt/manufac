import unittest
from datetime import timedelta

from codecs import open
from os import makedirs
from os.path import join,dirname, exists
from shutil import rmtree

from manufac.utils import FileCache
from manufac.importers.common import GraphScaffolding, parse_time, format_time
from manufac.importers.openscad import OpenSCADImporter
from manuallabour.core.common import Step
from manuallabour.core.stores import LocalMemoryStore
from manuallabour.core.graph import GraphStep
from manuallabour.exporters.svg import GraphSVGExporter

class TestYAML(unittest.TestCase):
    def setUp(self):
        self.store = LocalMemoryStore()
        cachedir = join('tests/output/.mlcache')
        if not exists(cachedir):
            makedirs(cachedir)
        self.cache = FileCache(cachedir)
        self.cache.clear()
        self.name = None
        self.scaf = None

    def tearDown(self):
        g = self.scaf.get_graph()
        e = GraphSVGExporter(with_resources=True,with_objects=True)
        e.export(
            g,
            self.store,
            join('tests','output','%s.svg' % self.name),
            author="John Does",
            title="Test"
        )

    def test_init(self):
        self.name = "simple"
        self.scaf = GraphScaffolding(
            'tests/yaml/simple.yaml',
            self.store,
            self.cache,
            []
        )

    def test_refs(self):
        self.name = "refs"
        self.scaf = GraphScaffolding(
            'tests/yaml/refs.yaml',
            self.store,
            self.cache,
            []
        )

    def test_openscad(self):
        os_imp = OpenSCADImporter('tests/yaml')

        self.name = "openscad"
        self.scaf = GraphScaffolding(
            'tests/yaml/openscad.yaml',
            self.store,
            self.cache,
            [os_imp]
        )

        print self.scaf.steps_out['s1']['images']
        self.assertEqual(
            len(self.scaf.steps_out['s1']['images']['chb']['sourcefiles']),
            2
        )

class TestTime(unittest.TestCase):
    def assertSeconds(self,time,seconds):
        self.assertEqual(timedelta(**parse_time(time)).total_seconds(),seconds)
    def test_parse(self):
        self.assertSeconds("4d",345600)
        self.assertSeconds("1 hour",3600)
        self.assertSeconds("3m",180)
        self.assertSeconds("2s",2)
        self.assertSeconds("3m2s",182)
        self.assertSeconds("1h3m2s",3782)
        self.assertSeconds("4d 1 hour 3m 2s",349382)
        self.assertSeconds("1 day 1 hour 1 minute 1 second",90061)
        self.assertSeconds("2 days 2 hours 2 minutes 2 seconds",180122)
        self.assertSeconds("2 d 2 h 2 m 2 s",180122)
        self.assertSeconds("2 d 2 h 2 min 2 s",180122)
        self.assertEqual(parse_time(None),None)
    def test_format(self):
        t = timedelta(days=3, hours=2, minutes=1, seconds = 7)
        self.assertEqual(t,timedelta(**parse_time(format_time(t))))

        self.assertEqual(format_time(None),None)


if __name__ == '__main__':
    unittest.main()
