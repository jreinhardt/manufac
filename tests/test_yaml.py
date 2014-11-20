import unittest

from os import makedirs
from os.path import join
from shutil import rmtree

from manuallabour.cl.utils import FileCache
from manuallabour.cl.importers.base import *
from manuallabour.cl.importers.openscad import OpenSCADImporter
from manuallabour.core.common import Step
from manuallabour.core.graph import GraphStep
from manuallabour.exporters.svg import GraphSVGExporter

class TestYAML(unittest.TestCase):
    def setUp(self):
        self.basic = BasicSyntaxImporter()
        self.store = LocalMemoryStore()
        self.steps = {}
        self.name = "test"

    def tearDown(self):
        steps = {}
        for alias,step_dict in self.steps.iteritems():
            requires = step_dict.pop("requires",[])
            step_id = Step.calculate_checksum(**step_dict)
            self.store.add_step(Step(step_id=step_id,**step_dict))

            steps[alias] = dict(step_id=step_id,requires=requires)

        g = Graph(graph_id="dummy",steps=steps)
        e = GraphSVGExporter(with_resources=True,with_objects=True)
        e.export(
            g,
            self.store,
            join('tests','output','%s.svg' % self.name),
            author="John Does",
            title="Test"
        )

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
