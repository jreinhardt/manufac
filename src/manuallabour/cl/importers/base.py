import yaml
from codecs import open
from os.path import join, basename, splitext, exists, dirname, abspath
from datetime import timedelta
import re
import json
import jsonschema
import pkg_resources
from copy import deepcopy

from manuallabour.core.stores import LocalMemoryStore
from manuallabour.core.graph import Graph, GraphStep
import manuallabour.core.common as common

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

class BasicSyntaxImporter(object):
    def _object_from_YAML(self,store,inst,created=False):
        # Object Reference properties
        quantity = inst.pop("quantity",1)
        optional = inst.pop("optional",False)

        # prepare resources
        images = []
        for img in inst.get("images",[]):
            images.append(self._image_from_YAML(store,img))
        inst["images"] = images

        # calculate obj id
        obj_id = common.Object.calculate_checksum(**inst)

        if not store.has_obj(obj_id):
            store.add_obj(common.Object(obj_id=obj_id,**inst))

        return common.ObjectReference(
            obj_id=obj_id,
            quantity=quantity,
            optional=optional,
            created=created
        )

    def _file_from_YAML(self,store,inst):
        path = inst["path"]
        filename = basename(path)
        with open(path,'rb') as fid:
            blob_id = common.calculate_blob_checksum(fid)
        if not store.has_blob(blob_id):
            store.add_blob(blob_id,path)

        res_id = common.File.calculate_checksum(filename=filename,blob_id=blob_id)

        if not store.has_res(res_id):
            store.add_res(common.File(res_id=res_id,blob_id=blob_id,filename=filename))

        return common.ResourceReference(res_id=res_id)

    def _image_from_YAML(self,store,inst):
        path = inst["filename"]
        ext = splitext(path)[1]
        alt = inst.get("alt","")

        with open(path,'rb') as fid:
            blob_id = common.calculate_blob_checksum(fid)
        if not store.has_blob(blob_id):
            store.add_blob(blob_id,path)

        res_id = common.Image.calculate_checksum(blob_id=blob_id,extension=ext,alt=alt)

        if not store.has_res(res_id):
            store.add_res(common.Image(res_id=res_id,blob_id=blob_id,extension=ext,alt=alt))

        return common.ResourceReference(res_id=res_id)

    def process(self,step_id,in_dict,out_dict,store,cache):
        step_in = in_dict["steps"][step_id]

        step_out = {}
        for prop in ["title","description"]:
            step_out[prop] = step_in[prop]

        if "waiting" in step_in:
            step_out["waiting"] = parse_time(step_in["waiting"])
        step_out["duration"] = parse_time(step_in["duration"])

        parts = {}
        for key, p_dict in step_in.get("parts",{}).iteritems():
            if "ref" in p_dict:
                continue
            parts[key] = self._object_from_YAML(store,p_dict)
        step_out["parts"] = parts

        tools = {}
        for key, t_dict in step_in.get("tools",{}).iteritems():
            if "ref" in t_dict:
                continue
            tools[key] = self._object_from_YAML(store,t_dict)
        step_out["tools"] = tools

        results = {}
        for key, r_dict in step_in.get("results",{}).iteritems():
            results[key] = self._object_from_YAML(store,r_dict,created=True)
        step_out["results"] = results

        images = {}
        for key, i_dict in step_in.get("images",{}).iteritems():
            images[key] = self._image_from_YAML(store,i_dict)
        step_out["images"] = images

        files = {}
        for key, f_dict in step_in.get("files",{}).iteritems():
            files[key] = self._file_from_YAML(store,f_dict)
        step_out["files"] = files

        dependencies = step_in.get('requires',[])
        if isinstance(dependencies,str):
            dependencies = [dependencies]
        step_out["requires"] = dependencies

        out_dict[step_id] = step_out

class ReferenceImporter(object):
    def _resolve_reference(self,ref_inst,out_dict):
        m = REF_RE.match(ref_inst.pop("ref"))
        target_step = m.group(1)
        target_key = m.group(2)
        obj_id = out_dict[target_step]["results"][target_key].obj_id

        quantity = ref_inst.get("quantity",1)
        optional = ref_inst.get("optional",False)

        return target_step,common.ObjectReference(
            obj_id=obj_id,
            quantity=quantity,
            optional=optional
        )

    def process(self,step_id,in_dict,out_dict,store,cache):
        step_in = in_dict["steps"][step_id]
        step_out = out_dict[step_id]

        for key, p_dict in step_in.get("parts",{}).iteritems():
            if "ref" in p_dict:
                target_step,obj_ref = self._resolve_reference(
                    p_dict,
                    out_dict
                )

                if target_step not in step_out["requires"]:
                    step_out["requires"].append(target_step)

                step_out["parts"][key] = obj_ref

        for key, t_dict in step_in.get("tools",{}).iteritems():
            if "ref" in t_dict:
                target_step,obj_ref = self._resolve_reference(
                    t_dict,
                    out_dict
                )

                if target_step not in step_out["requires"]:
                    step_out["requires"].append(target_step)

                step_out["tools"][key] = obj_ref
