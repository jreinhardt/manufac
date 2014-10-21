import yaml
from codecs import open
from os.path import join, basename, splitext, exists, dirname, abspath
from datetime import timedelta
import re
import json
import jsonschema
import pkg_resources
import hashlib
from copy import deepcopy

import manuallabour.core as core

schema_dir = pkg_resources.resource_filename('manuallabour.cl','schema')

TIME_RE = re.compile("(?:(\d*)\s?d(?:ays?)?\s?)?(?:(\d*)\s?h(?:ours?)?\s?)?(?:(\d*)\s?m(?:in(?:ute)?s?)?\s?)?(?:(\d*) ?s(?:econds?)?)?")
TIME_ZIP = ('days','hours','minutes','seconds')

REF_RE = re.compile("^([a-zA-Z][0-9a-zA-Z]*)\.results\.([a-zA-Z][0-9a-zA-Z]*)$")

def parse_time(time):
    """
    parse a string of the form
    "x d[ay[s]] y h[our[s]] z m[inute[s]] w s[econd[s]]"
    into a timedelta object
    passes through None
    """
    if time is None:
        return None
    match = TIME_RE.match(time.strip())
    components = dict(zip(TIME_ZIP,(int(v) for v in match.groups('0'))))
    return timedelta(**components)

def format_time(time):
    """
    format a timedelta object in such a way that it can be recreated with
    parse_time
    passes through None
    """
    if time is None:
        return None
    res = []
    if time.days > 0:
        res.append("%d days" % time.days)
    seconds = time.seconds
    if seconds >= 3600:
        res.append("%d hours" % (seconds / 3600))
        seconds = seconds % 3600
    if seconds >= 60:
        res.append("%d minutes" % (seconds / 60))
        seconds = seconds % 60
    if seconds > 0:
        res.append("%d seconds" % seconds)

    return " ".join(res)


def validate(inst,schema_name):
    schema_path = abspath(join(schema_dir,schema_name))
    schema = json.loads(open(schema_path).read())
    res = jsonschema.RefResolver('file://' + schema_path,schema)
    val = jsonschema.Draft4Validator(schema,resolver=res)
    val.validate(inst)

def add_object_from_YAML(store,inst,created=False):
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

    return core.ObjectReference(
        obj_id,
        quantity=quantity,
        optional=optional,
        created=created
    )

def resolve_reference(store,ref_inst,steps):
    m = REF_RE.match(ref_inst.pop("ref"))
    target_step = m.group(1)
    target_key = m.group(2)
    target_dict = deepcopy(steps[target_step]["results"][target_key])

    # calculate obj id
    m = hashlib.sha512()
    m.update(target_dict.get('name'))
    m.update(target_dict.get('description',''))
    obj_id = m.hexdigest()

    # prepare resources
    images = []
    for img in target_dict.get("images",[]):
        images.append(add_image_from_YAML(store,img))
    target_dict["images"] = images

    #we don't need this information from the target reference, so discard it
    target_dict.pop("quantity",None)
    target_dict.pop("optional",None)

    if not store.has_obj(obj_id):
        store.add_obj(core.Object(obj_id,**target_dict))

    quantity = ref_inst.get("quantity",1)
    optional = ref_inst.get("optional",False)

    return core.ObjectReference(obj_id, quantity=quantity, optional=optional)

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
        for key, p_dict in step_dict.get("parts",{}).iteritems():
            if "ref" in p_dict:
                parts[key] = resolve_reference(store,p_dict,inst["steps"])
            else:
                parts[key] = add_object_from_YAML(store,p_dict)
        step_dict["parts"] = parts

        tools = {}
        for key, t_dict in step_dict.get("tools",{}).iteritems():
            if "ref" in t_dict:
                tools[key] = resolve_reference(store,t_dict,inst["steps"])
            else:
                tools[key] = add_object_from_YAML(store,t_dict)
        step_dict["tools"] = tools

        results = {}
        for key, r_dict in step_dict.get("results",{}).iteritems():
            results[key] = add_object_from_YAML(store,r_dict,created=True)
        step_dict["results"] = results

        images = {}
        for key, i_dict in step_dict.get("images",{}).iteritems():
            images[key] = add_image_from_YAML(store,i_dict)
        step_dict["images"] = images

        files = {}
        for key, f_dict in step_dict.get("files",{}).iteritems():
            files[key] = add_file_from_YAML(store,f_dict)
        step_dict["files"] = files

        step = core.GraphStep(id,**step_dict)

        g.add_step(step,dependencies)

    return g
