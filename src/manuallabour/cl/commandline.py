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
        choices=['deck','bootstrap'],
        default='deck'
    )
    parser.add_argument(
        '-c',
        help='clear cache before processing',
        dest='clearcache',
        action='store_true'
    )

    args = vars(parser.parse_args())

    inst = list(yaml.load_all(open(args['input'],"r","utf8")))[0]

    #validate
    #validate(inst,'ml.json')

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
    reqs = {}

    # base syntax
    for step_id in inst["steps"]:
        basic_imp.process(step_id,inst,steps,reqs,store,None)

    # importers
    with FileCache(cachedir) as fc:
        if args["clearcache"]:
            fc.clear()
        for imp in importers:
            for step_id,step_dict in inst["steps"].iteritems():
                imp.process(step_id,inst,steps,reqs,store,fc)

    # references
    for step_id in inst["steps"]:
        ref_imp.process(step_id,inst,steps,reqs,store,None)


    g = Graph(store)
    for step_id in steps:
        g.add_step(GraphStep(step_id,**steps[step_id]),reqs[step_id])

    steps,start = schedule_greedy(g)

    s = Schedule(steps,g.store,start)

    s.to_svg(join(args['output'],'schedule.svg'))
