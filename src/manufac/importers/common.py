from manuallabour.core.graph import Graph, GraphStep
import pkg_resources
import re
import json
import jsonschema
from codecs import open

from os.path import join,dirname, exists, abspath, splitext, basename
import yaml

import manuallabour.core.common as common

schema_dir = pkg_resources.resource_filename('manufac','schema')

TIME_RE = re.compile("(?:(\d*)\s?d(?:ays?)?\s?)?(?:(\d*)\s?h(?:ours?)?\s?)?(?:(\d*)\s?m(?:in(?:ute)?s?)?\s?)?(?:(\d*) ?s(?:econds?)?)?")
TIME_ZIP = ('days','hours','minutes','seconds')

REF_RE = re.compile("^([a-zA-Z][0-9a-zA-Z]*)\.results\.([a-zA-Z][0-9a-zA-Z]*)$")

GRAPH_REF_RE = re.compile("^([a-zA-Z][0-9a-zA-Z]*)\.([a-zA-Z][0-9a-zA-Z]*)$")

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
    return dict(zip(TIME_ZIP,(int(v) for v in match.groups('0'))))

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

class GraphScaffolding(object):
    """
    Class to build up a graph. Holds the raw data from the YAML and
    coordinates the importers.
    """
    def __init__(self,inputfile,store,filecache,importers):
        self.store = store
        self.cache = filecache

        inst = list(yaml.load_all(open(inputfile,"r","utf8")))[0]
        validate(inst,'ml.json')

        basedir = dirname(inputfile)

        self.steps_raw = inst["steps"]
        self.steps_out = {}
        self.step_ids = {}
        self.graph_steps = {}
        self.included_steps = {}

        #load includes
        self.include = {}
        for alias, filename in inst.get("include",{}).iteritems():
            self.include[alias] = GraphScaffolding(
                join(basedir,filename),
                store,
                filecache,
                importers
            )

        #parse base syntax
        for alias, raw in self.steps_raw.iteritems():
            out = self.steps_out.setdefault(alias,{})

            for prop in ["title","description"]:
                out[prop] = raw[prop]

            out["duration"] = parse_time(raw["duration"])
            if "waiting" in raw:
                out["waiting"] = parse_time(raw["waiting"])

            for nspace in ["parts","tools"]:
                objs = out.setdefault(nspace,{})
                for key, o_dict in raw.get(nspace,{}).iteritems():
                    if "ref" in o_dict:
                        continue
                    objs[key] = self._object_from_YAML(o_dict)

            results = out.setdefault("results",{})
            for key, r_dict in raw.get("results",{}).iteritems():
                results[key] = self._object_from_YAML(r_dict,created=True)

            images = out.setdefault("images",{})
            for key, i_dict in raw.get("images",{}).iteritems():
                images[key] = self._image_from_YAML(i_dict)

            files = out.setdefault("files",{})
            for key, f_dict in raw.get("files",{}).iteritems():
                files[key] = self._file_from_YAML(f_dict)

        #run importers
        with filecache as fc:
            for imp in importers:
                imp.process(self)

        #dereference objects
        for alias, raw in self.steps_raw.iteritems():
            out = self.steps_out.setdefault(alias,{})
            for nspace in ["parts","tools"]:
                objs = out.setdefault(nspace,{})
                for key, o_dict in raw.get(nspace,{}).iteritems():
                    if "ref" in o_dict:
                        objs[key] = self._resolve_reference(o_dict)

        #step contents are finished now

        #step_ids
        for alias, step in self.steps_out.iteritems():
            step_id = common.Step.calculate_checksum(**step)
            self.step_ids[alias] = step_id
            if not store.has_step(step_id):
                store.add_step(common.Step(step_id=step_id,**step))

        #build graph_steps
        for alias, raw in self.steps_raw.iteritems():
            ref = self.graph_steps.setdefault(alias,dict(requires=set([])))

            #requirements from base syntax
            dependencies = raw.get('requires',[])
            if isinstance(dependencies,str):
                dependencies = [dependencies]
            for dep in dependencies:
                match = GRAPH_REF_RE.match(dep)
                if match is None:
                    ref["requires"].add(self.step_ids[dep])
                else:
                    target_scaf = self.include[match.group(1)]
                    target_step_id = target_scaf.step_ids[match.group(2)]
                    ref["requires"].add(target_step_id)
                    inc_steps = self.included_steps.setdefault(match.group(1),[])
                    inc_steps.append(target_step_id)

            #requirements from references
            for nspace in ["parts","tools"]:
                for key, o_dict in raw.get(nspace,{}).iteritems():
                    if "ref" in o_dict:
                        match = REF_RE.match(o_dict.get("ref"))
                        target_alias = match.group(1)
                        ref["requires"].add(self.step_ids[target_alias])
            ref["requires"] = list(ref["requires"])


    def get_graph(self):
        steps = []
        #from this graph scaffolding
        for alias,step in self.graph_steps.iteritems():
            steps.append(dict(step_id=self.step_ids[alias],**step))

        #from includes
        for scaf, step_ids in self.included_steps.iteritems():
            inc_steps = set([])
            graph = self.include[scaf].get_graph()
            for step_id in step_ids:
                inc_steps.add(step_id)
                inc_steps.update(graph.all_ancestors(step_id))

            for graph_step in graph.steps:
                if graph_step.step_id in inc_steps:
                    steps.append(graph_step.as_dict())

        graph_id = Graph.calculate_checksum(steps=steps)
        return Graph(graph_id=graph_id,steps=steps)

    def _object_from_YAML(self,inst,created=False):
        # Object Reference properties
        ref = dict(
            quantity = inst.get("quantity",1),
            optional = inst.get("optional",False),
            created = created
        )

        # Object properties
        obj = dict(images=[])

        #prepare resources
        for img in inst.get("images",[]):
            obj["images"].append(self._image_from_YAML(img))

        #copy remaining fields
        for key in inst:
            if not key in ref and not key in obj:
                obj[key] = inst.get(key)

        # calculate obj id
        obj_id = common.Object.calculate_checksum(**obj)

        if not self.store.has_obj(obj_id):
            self.store.add_obj(common.Object(obj_id=obj_id,**obj))

        return dict(obj_id=obj_id,**ref)

    def _file_from_YAML(self,inst):
        path = inst["path"]
        filename = basename(path)
        with open(path,'rb') as fid:
            blob_id = common.calculate_blob_checksum(fid)
        if not self.store.has_blob(blob_id):
            self.store.add_blob(blob_id,path)

        return dict(blob_id=blob_id,filename=filename)

    def _image_from_YAML(self,inst):
        path = inst["filename"]
        ext = splitext(path)[1]
        alt = inst.get("alt","")

        with open(path,'rb') as fid:
            blob_id = common.calculate_blob_checksum(fid)
        if not self.store.has_blob(blob_id):
            self.store.add_blob(blob_id,path)

        return dict(blob_id=blob_id,extension=ext,alt=alt)

    def _resolve_reference(self,ref_inst):
        m = REF_RE.match(ref_inst["ref"])
        target_step = m.group(1)
        target_key = m.group(2)
        obj_id = self.steps_out[target_step]["results"][target_key]["obj_id"]

        quantity = ref_inst.get("quantity",1)
        optional = ref_inst.get("optional",False)

        return dict(
            obj_id=obj_id,
            quantity=quantity,
            optional=optional
        )

    def get_step_id(alias):
        return Step.calculate_checksum(**self.steps_out[alias])

class ImporterBase(object):
    """
    Base Class for importers
    """
    def __init__(self,key):
        """
        Name of the key in the step dictionary this importer takes care of.
        """
        self.key = key

    def process(self,scaf):
        """
        Process graph
        """
        pass
