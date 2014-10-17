import yaml
from codecs import open
from os.path import join, basename, splitext, exists, dirname, abspath
from datetime import timedelta
import re
import json
import jsonschema
import pkg_resources
import hashlib

import manuallabour.core as core

schema_dir = pkg_resources.resource_filename('manuallabour.cl','schema')

time_re = re.compile("(?:(\d*)\s?d(?:ays?)?\s?)?(?:(\d*)\s?h(?:ours?)?\s?)?(?:(\d*)\s?m(?:in(?:ute)?s?)?\s?)?(?:(\d*) ?s(?:econds?)?)?")
time_zip = ('days','hours','minutes','seconds')

def parse_time(time):
    match = time_re.match(time.strip())
    components = dict(zip(time_zip,(int(v) for v in match.groups('0'))))
    return timedelta(**components)

def validate(inst,schema_name):
    schema_path = abspath(join(schema_dir,schema_name))
    schema = json.loads(open(schema_path).read())
    res = jsonschema.RefResolver('file://' + schema_path,schema)
    val = jsonschema.Draft4Validator(schema,resolver=res)
    val.validate(inst)

def add_object_from_YAML(graph,inst):
    quantity = inst.pop("quantity",1)
    optional = inst.pop("optional",False)

    m = hashlib.sha512()
    m.update(inst.get('name'))
    m.update(inst.get('description',''))

    obj_id = m.hexdigest()

    if not obj_id in graph.objects:
        graph.add_object(core.Object(obj_id,**inst))

    return core.ObjectReference(obj_id,quantity=quantity,optional=optional)

def graph_from_YAML(filename):
    inst = list(yaml.load_all(open(filename,"r","utf8")))[0]

    #validate
    validate(inst,'ml.json')

    g = core.Graph()

    for id,step_dict in inst["steps"].iteritems():
        if "waiting" in step_dict:
            step_dict["waiting"] = parse_time(step_dict.pop("waiting"))
        step_dict["duration"] = parse_time(step_dict.pop("duration"))

        dependencies = step_dict.pop('requires',[])
        if isinstance(dependencies,str):
            dependencies = [dependencies]

        parts = {}
        for key, inst in step_dict.get("parts",{}).iteritems():
            parts[key] = add_object_from_YAML(g,inst)
        step_dict["parts"] = parts

        tools = {}
        for key, inst in step_dict.get("tools",{}).iteritems():
            tools[key] = add_object_from_YAML(g,inst)
        step_dict["tools"] = tools

        step = core.GraphStep(id,**step_dict)

        g.add_step(step,dependencies)

    return g
