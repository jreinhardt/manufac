import click
import sys
from os.path import join,dirname, exists
from os import makedirs
from copy import copy
from codecs import open
from pkg_resources import iter_entry_points

import yaml
import requests
from requests.auth import HTTPBasicAuth
import json

from manuallabour.core.schedule import schedule_greedy, Schedule
from manuallabour.core.stores import LocalMemoryStore
from manuallabour.core.common import Step
from manuallabour.core.graph import Graph,GraphStep
from manuallabour.exporters.html import SinglePageHTMLExporter
from manuallabour.exporters.ttn import ThingTrackerExporter
from manuallabour.exporters.svg import GraphSVGExporter, ScheduleSVGExporter
from manuallabour.cl.utils import FileCache
from manuallabour.cl.importers.base import *

def load_graph(input_file,store,clear_cache):
    inst = list(yaml.load_all(open(input_file,"r","utf8")))[0]

    validate(inst,'ml.json')

    basedir = dirname(input_file)

    basic_imp = BasicSyntaxImporter()
    ref_imp = ReferenceImporter()

    importers = []
    for ep in iter_entry_points('importers'):
        importers.append(ep.load()(basedir))

    cachedir = join(basedir,'.mlcache')
    if not exists(cachedir):
        makedirs(cachedir)

    steps = {}

    # base syntax
    for step_alias in inst["steps"]:
        basic_imp.process(step_alias,inst,steps,store,None)

    # importers
    with FileCache(cachedir) as fc:
        for imp in importers:
            for step_alias,step_dict in inst["steps"].iteritems():
                imp.process(step_alias,inst,steps,store,fc)

    # resolve references
    for step_alias in inst["steps"]:
        ref_imp.process(step_alias,inst,steps,store,None)

    # create steps
    graph_steps = []
    step_alia = {}
    for alias, step_dict in steps.iteritems():
        requires = step_dict.pop("requires",[])

        step_id = Step.calculate_checksum(**step_dict)
        store.add_step(Step(step_id=step_id,**step_dict))

        step_alia[alias] = step_id

        graph_steps.append(dict(step_id=step_id,requires=requires))

    graph_id = Graph.calculate_checksum(steps=graph_steps)
    return Graph(graph_id=graph_id,steps=graph_steps), step_alia

@click.group()
def cli():
    """
    """
    pass

@cli.command()
@click.argument('input_file',type=click.Path(exists=True))
def clean(input_file):
    basedir = dirname(input_file)

    #clear cache
    cachedir = join(basedir,'.mlcache')
    if exists(cachedir):
        with FileCache(cachedir) as fc:
            fc.clear()


@cli.command()
@click.option('-o','--output',type=click.Path(exists=False,file_okay=False,dir_okay=True),default='docs')
@click.option('-f','--format',type=click.Choice(['html','ttn']),default='html')
@click.option('-l','--layout',default='basic')
@click.argument('input_file',type=click.Path(exists=True))
def render(output,format,layout,input_file):
    """
    Render the instructions
    """
    inst = list(yaml.load_all(open(input_file,"r","utf8")))[0]

    store = LocalMemoryStore()

    graph,_ = load_graph(input_file,store)

    schedule_steps = schedule_greedy(graph,store)

    s = Schedule(sched_id="dummy",steps = schedule_steps)

    data = dict(title=inst["title"],author="John Doe")

    if format == "html":
        e = SinglePageHTMLExporter(layout)
        e.export(s,store,output,**data)

        e = ScheduleSVGExporter(with_resources=True,with_objects=True)
        e.export(s,store,join(output,'schedule.svg'),**data)

        e = GraphSVGExporter(with_resources=True,with_objects=True)
        e.export(graph,store,join(output,'graph.svg'),**data)
    elif format == "ttn":
        e = ThingTrackerExporter()

        e.export(s,store,join(output,'tracker.json'),**data)

@cli.command()
@click.option('-h','--host',default='http://flask.dev:5000/')
@click.option('--username',prompt=True)
@click.option('--password',prompt=True, hide_input=True)
@click.argument('input_file',type=click.Path(exists=True))
@click.argument('graph_name')
def upload(host,username,password,input_file,graph_name):
    """
    Upload the instruction to a cadinet
    """

    inst = list(yaml.load_all(open(input_file,"r","utf8")))[0]

    store = LocalMemoryStore()

    graph,_ = load_graph(input_file,store)
    url = "%s%s" % (host,"%s")
    headers = {'content-type' : 'application/json'}
    auth=HTTPBasicAuth(username,password)

    #check what needs to be uploaded
    ids = graph.collect_ids(store)
    ids["graph_ids"] = [graph.graph_id]
    r = requests.get(
        url % "exist",
        data=json.dumps(ids),
        auth=auth,
        headers=headers
    )
    print r.content
    unknown = r.json()

    #upload blobs
    for blob_id in unknown["blob_ids"]:
        path = store.get_blob_url(blob_id)
        fid = urlopen(store.get_blob_url(blob_id))
        files = {'file' : (basename(path),fid)}
        r = requests.post(
            url % "upload/blob",
            files=files,
            auth=auth
        )
        assert(r.json()["blob_id"]==blob_id)
    if unknown["blob_ids"]:
        print "Uploaded %d blobs" % len(unknown["blob_ids"])

    #upload objects
    for obj_id in unknown["obj_ids"]:
        data = store.get_obj(obj_id).as_dict()
        data.pop("obj_id")
        r = requests.post(
            url % "upload/object",
            data = json.dumps(data),
            auth=auth,
            headers=headers
        )
        assert(r.json()["obj_id"]==obj_id)
    if unknown["obj_ids"]:
        print "Uploaded %d objects" % len(unknown["obj_ids"])

    #upload steps
    for step_id in unknown["step_ids"]:
        data = store.get_step(step_id).as_dict()
        data.pop("step_id")
        r = requests.post(
            url % "upload/step",
            data = json.dumps(data),
            auth=auth,
            headers=headers
        )
        assert(r.json()["step_id"]==step_id)
    if unknown["step_ids"]:
        print "Uploaded %d steps" % len(unknown["step_ids"])

    #upload graph
    if unknown["graph_ids"]:
        data = g.as_dict()
        data.pop("graph_id")
        r = requests.post(
            url % "upload/graph",
            data = json.dumps(data),
            auth=auth,
            headers=headers
        )
        assert(r.json()["graph_id"]==graph.graph_id)
        print "Uploaded graph with id: %s" % graph.graph_id

    #register graph
    r = requests.post(
        url % ("graphs/%s/%s" % (username,graph_name)),
        data = json.dumps({
            "graph_id" : graph.graph_id,
            "title" : inst["title"],
            "author" : "John Doe"
        }),
        auth=auth,
        headers=headers
    )
    print "Registered graph as %s" % graph_name
