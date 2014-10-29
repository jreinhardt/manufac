import unittest

from os import makedirs
from os.path import join
from shutil import rmtree

from manuallabour.cl.utils import FileCache
from manuallabour.cl.importers.base import *
from manuallabour.cl.importers.openscad import OpenSCADImporter

class TestYAML(unittest.TestCase):
    def setUp(self):
        self.basic = BasicSyntaxImporter()
        self.store = LocalMemoryStore()
        self.steps = {}
        self.name = "test"

    def tearDown(self):
        steps = []
        for step_id,step in self.steps.iteritems():
            steps.append(GraphStep(step_id,**step))
        g = Graph(steps,self.store)
        g.to_svg(join('tests','output','%s.svg' % self.name))

    def test_init(self):
        inst = list(
            yaml.load_all(open('tests/yaml/simple.yaml',"r","utf8"))
        )[0]

        self.name = "simple"

        for step_id in inst["steps"]:
            self.basic.process(step_id,inst,self.steps,self.store,None)

    def test_refs(self):
        inst = list(
            yaml.load_all(open('tests/yaml/refs.yaml',"r","utf8"))
        )[0]

        self.name = "refs"

        ref_imp = ReferenceImporter()

        for step_id in inst["steps"]:
            self.basic.process(step_id,inst,self.steps,self.store,None)

        for step_id in inst["steps"]:
            ref_imp.process(step_id,inst,self.steps,self.store,None)

    def test_openscad(self):
        inst = list(
            yaml.load_all(open('tests/yaml/openscad.yaml',"r","utf8"))
        )[0]

        self.name = "openscad"

        cachedir  = join('tests','cache',self.name)
        rmtree(cachedir,True)
        makedirs(cachedir)

        basic_imp = BasicSyntaxImporter()
        ref_imp = ReferenceImporter()
        os_imp = OpenSCADImporter('tests/yaml')

        for step_id in inst["steps"]:
            basic_imp.process(step_id,inst,self.steps,self.store,None)

        with FileCache(cachedir) as cache:
            for step_id in inst["steps"]:
                os_imp.process(step_id,inst,self.steps,self.store,cache)

        for step_id,step_dict in inst["steps"].iteritems():
            ref_imp.process(step_id,inst,self.steps,self.store,None)

        with open(join(cachedir,'.deps')) as fid:
            deps = json.loads(fid.read())
        self.assertEqual(len(deps),5)
        for dep in deps.values():
            self.assertEqual(len(dep),2)

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
