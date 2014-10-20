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

def add_object_from_YAML(store,inst):
    # Object Reference properties
    quantity = inst.pop("quantity",1)
    optional = inst.pop("optional",False)

    # calculate obj id
    m = hashlib.sha512()
    m.update(inst.get('name'))
    m.update(inst.get('description',''))
    obj_id = m.hexdigest()

    # prepare resources
    images = []
    for img in inst.get("images",[]):
        images.append(add_image_from_YAML(store,img))
    inst["images"] = images

    if not store.has_obj(obj_id):
        store.add_obj(core.Object(obj_id,**inst))

    return core.ObjectReference(obj_id,quantity=quantity,optional=optional)

def add_file_from_YAML(store,inst):
    path = inst["path"]

    res_id = hashlib.sha512(path).hexdigest()

    if not store.has_res(res_id):
        store.add_res(core.File(res_id,filename=basename(path)),path)

    return core.ResourceReference(res_id)

def add_image_from_YAML(store,inst):
    path = inst["filename"]
    ext = splitext(path)[1]
    alt = inst.get("alt","")

    res_id = hashlib.sha512(path).hexdigest()

    if not store.has_res(res_id):
        store.add_res(core.Image(res_id,extension=ext,alt=alt),path)

    return core.ResourceReference(res_id)

def graph_from_YAML(filename):
    inst = list(yaml.load_all(open(filename,"r","utf8")))[0]

    #validate
    validate(inst,'ml.json')

    store = core.LocalMemoryStore()

    g = core.Graph(store)

    for id,step_dict in inst["steps"].iteritems():
        if "waiting" in step_dict:
            step_dict["waiting"] = parse_time(step_dict.pop("waiting"))
        step_dict["duration"] = parse_time(step_dict.pop("duration"))

        dependencies = step_dict.pop('requires',[])
        if isinstance(dependencies,str):
            dependencies = [dependencies]

        parts = {}
        for key, inst in step_dict.get("parts",{}).iteritems():
            parts[key] = add_object_from_YAML(store,inst)
        step_dict["parts"] = parts

        tools = {}
        for key, inst in step_dict.get("tools",{}).iteritems():
            tools[key] = add_object_from_YAML(store,inst)
        step_dict["tools"] = tools

        images = {}
        for key, inst in step_dict.get("images",{}).iteritems():
            images[key] = add_image_from_YAML(store,inst)
        step_dict["images"] = images

        files = {}
        for key, inst in step_dict.get("files",{}).iteritems():
            files[key] = add_file_from_YAML(store,inst)
        step_dict["files"] = files

        step = core.GraphStep(id,**step_dict)

        g.add_step(step,dependencies)

    return g
