import argparse
import sys
from os.path import join,dirname, exists
from os import makedirs
from copy import copy
from codecs import open
from pkg_resources import iter_entry_points

import yaml

from manuallabour.core.schedule import schedule_greedy, Schedule
from manuallabour.core.stores import LocalMemoryStore
from manuallabour.core.common import Step
from manuallabour.core.graph import Graph,GraphStep
from manuallabour.exporters.html import SinglePageHTMLExporter
from manuallabour.cl.utils import FileCache
from manuallabour.cl.importers.base import *

def main_function():
    parser = argparse.ArgumentParser(
        description="Tool for rendering beautiful step-by-step instructions"
    )
    parser.add_argument(
        'input',
        help='input yaml file',
        type=str
    )
    parser.add_argument(
        '-o',
        help='output directory',
        dest='output',
        type=str,
        default='docs'
    )
    parser.add_argument(
        '-f',
        help='export format',
        dest='format',
        type=str,
        choices=['html','text'],
        default='html'
    )
    parser.add_argument(
        '-l',
        help='layout (for html only)',
        dest='layout',
        type=str,
        default='basic'
    )
    parser.add_argument(
        '-c',
        help='clear cache before processing',
        dest='clearcache',
        action='store_true'
    )

    args = vars(parser.parse_args())

    inst = list(yaml.load_all(open(args['input'],"r","utf8")))[0]

    data = dict(title=inst["title"],author="John Doe")

    validate
    validate(inst,'ml.json')

    basedir = dirname(args['input'])

    basic_imp = BasicSyntaxImporter()
    ref_imp = ReferenceImporter()

    importers = []
    for ep in iter_entry_points('importers'):
        importers.append(ep.load()(basedir))

    cachedir = join(basedir,'.mlcache')
    if not exists(cachedir):
        makedirs(cachedir)

    store = LocalMemoryStore()

    steps = {}

    # base syntax
    for step_id in inst["steps"]:
        basic_imp.process(step_id,inst,steps,store,None)

    # importers
    with FileCache(cachedir) as fc:
        if args["clearcache"]:
            fc.clear()
        for imp in importers:
            for step_id,step_dict in inst["steps"].iteritems():
                imp.process(step_id,inst,steps,store,fc)

    # resolve references
    for step_id in inst["steps"]:
        ref_imp.process(step_id,inst,steps,store,None)

    # create steps
    graph_steps = {}
    for alias, step_dict in steps.iteritems():
        requires = step_dict.pop("requires",[])

        step_id = Step.calculate_checksum(**step_dict)
        store.add_step(Step(step_id=step_id,**step_dict))

        graph_steps[alias] = GraphStep(step_id=step_id,requires=requires)

    g = Graph(graph_steps,store)

    schedule_steps = schedule_greedy(g)

    s = Schedule(schedule_steps,g.store)

    e = SinglePageHTMLExporter(args['layout'])
    e.export(s,args['output'],**data)
    s.to_svg(join(args['output'],'schedule.svg'))

