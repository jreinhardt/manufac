from manuallabour.core.stores import LocalMemoryStore
from manuallabour.exporters.svg import GraphSVGExporter
from manufac.pv_loader import verse, load_graph
from os.path import join,dirname, exists, basename
from unittest import TestCase
from pprint import pformat

verses = [
    "Insert 1 thing into the qualification of the target",
    "Insert 3 M3 Bolts into the holes of the back housing",
    "Attach the lever to the left side of the frame as shown in lever.png",
    "Screw a M3 Bolt into the flange with a screwdriver",
    "Clip four attachments (shown in attach.png) into the slots of the body",
    "Tighten a M3 Bolt (see bolt.png) and 2 M3 Nuts onto the carriage using "
    "a M3 wrench and a M3 screwdriver to form the x carriage assembly",
    "Fix that to the main assembly to finish the printer"
]

class VerseTest(TestCase):
    def test_verses(self):
        for v in verses:
            print v
            print verse.parseString(v)

class TestPV(TestCase):
    def setUp(self):
        self.store = LocalMemoryStore()
        self.name = None
        self.graph = None
    def tearDown(self):
        e = GraphSVGExporter(with_resources=True,with_objects=True)
        e.export(
            self.graph,
            self.store,
            join('tests','output','pv-%s.svg' % self.name),
            author="John Does",
            title="Test"
        )
        with open(join('tests','output','pv-%s.txt' % self.name),'w') as fid:
            fid.write(pformat(self.graph.dereference(self.store)))
    def test_simple(self):
        self.name = "simple"
        self.graph = load_graph(
            'tests/pv/simple.pv',
            self.store,
            "tests/pv"
            )
    def test_assign(self):
        self.name = "assign"
        self.graph = load_graph(
            'tests/pv/assign.pv',
            self.store,
            "tests/pv"
            )
        step_dict = self.graph.steps[2].dereference(self.store)
        self.assertEqual(step_dict["title"],"Attach the bar")
    def test_tools(self):
        self.name = "tools"
        self.graph = load_graph(
            'tests/pv/tools.pv',
            self.store,
            "tests/pv"
            )
    def test_images(self):
        self.name = "images"
        self.graph = load_graph(
            'tests/pv/images.pv',
            self.store,
            "tests/pv"
            )
    def test_complete(self):
        self.name = "complete"
        self.graph = load_graph(
            'tests/pv/complete.pv',
            self.store,
            "tests/pv"
            )
