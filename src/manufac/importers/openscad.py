from manufac.importers.common import ImporterBase
from tempfile import mkstemp
from subprocess import call
import os
import hashlib
from os.path import basename, splitext

import manuallabour.core.common as common
from manuallabour.core.common import calculate_blob_checksum

class OpenSCADImporter(ImporterBase):
    def __init__(self,basedir):
        ImporterBase.__init__(self,'openscad')
        self.basedir = basedir

    def _extract_dependencies(self,dep_path,tmps):
        lines = open(dep_path).readlines()
        deps = []
        lines.pop(0)
        for line in lines:
            dep = line.strip(" \n\t\\")
            if not dep in tmps:
                deps.append(dep)
        return deps

    def _image(self,target,**kwargs):
        args = ["openscad","-o",target]

        #dependencies
        dep_fd, dep_path = mkstemp(suffix=".deps",dir=self.basedir)
        args.append("-d")
        args.append(dep_path)

        if "size" in kwargs:
            args.append('--imgsize=%d,%d' % tuple(kwargs["size"]))
        if "camera" in kwargs:
            args.append('--camer=%d,%d,%d,0,0,0' % tuple(kwargs["camera"]))

        if "module" in kwargs:
            fd, tpath = mkstemp(suffix=".scad",dir=self.basedir)
            fid = os.fdopen(fd,'w')
            fid.write("use <%s>\n" % kwargs["scadfile"])
            if "parameters" in kwargs:
                fid.write("%s(%s);\n" % (kwargs["module"],",".join([str(p) for p in kwargs["parameters"]])))
            else:
                fid.write("%s();\n" % kwargs["module"])

            fid.close()

            args.append(tpath)
            call(args,stdout=open(os.devnull,'w'),stderr=open(os.devnull,'w'))
            os.remove(tpath)
        else:
            args.append(join(self.basedir,kwargs["scadfile"]))
            call(args,stdout=open(os.devnull,'w'),stderr=open(os.devnull,'w'))

        #extract dependencies
        deps = self._extract_dependencies(dep_path,tpath)
        os.remove(dep_path)
        return deps

    def _file(self,target,**kwargs):
        args = ["openscad","-o",target]

        #dependencies
        dep_fd, dep_path = mkstemp(suffix=".deps",dir=self.basedir)
        args.append("-d")
        args.append(dep_path)

        if "module" in kwargs:
            fd, tpath = mkstemp(suffix=".scad",dir=self.basedir)
            fid = os.fdopen(fd,'w')
            fid.write("use <%s>\n" % kwargs["scadfile"])
            if "parameters" in kwargs:
                fid.write("%s(%s);\n" % (kwargs["module"],",".join([str(p) for p in kwargs["parameters"]])))
            else:
                fid.write("%s();\n" % kwargs["module"])

            fid.close()

            args.append(tpath)
            call(args,stdout=open(os.devnull,'w'),stderr=open(os.devnull,'w'))
            os.remove(tpath)
        else:
            args.append(join(self.basedir,kwargs["scadfile"]))
            call(args,stdout=open(os.devnull,'w'),stderr=open(os.devnull,'w'))

        #extract dependencies
        deps = self._extract_dependencies(dep_path,tpath)
        os.remove(dep_path)
        return deps

    def process(self,scaf):
        for alias, step_dict in scaf.steps_raw.iteritems():
            out = scaf.steps_out[alias]
            if not 'openscad' in step_dict:
                continue
            openscad = step_dict["openscad"]

            if "images" in openscad:
                for id,item in openscad["images"].iteritems():
                    path,deps = scaf.cache.process(
                        self._image,
                        importer='openscad',
                        extension='.png',
                        **item)
                    with open(path,'rb') as fid:
                        blob_id = calculate_blob_checksum(fid)
                    if not scaf.store.has_blob(blob_id):
                        scaf.store.add_blob(blob_id,path)

                    img_dict = dict(
                        blob_id=blob_id,
                        extension='.png',
                        alt='Render of %s' % item['scadfile'],
                        sourcefiles=[]
                    )
                    if not deps is None:
                        for dep in deps:
                            with open(dep,'rb') as fid:
                                dep_id = calculate_blob_checksum(fid)
                            if not scaf.store.has_blob(dep_id):
                                scaf.store.add_blob(dep_id,dep)
                            img_dict["sourcefiles"].append(dict(
                                blob_id=dep_id,
                                filename=basename(dep)
                            ))

                    out['images'][id] = img_dict

            if "files" in openscad:
                for id,item in openscad["files"].iteritems():
                    path,deps = scaf.cache.process(
                        self._file,
                        importer='openscad',
                        extension=splitext(item['filename'])[1],
                        **item)
                    with open(path,'rb') as fid:
                        blob_id = calculate_blob_checksum(fid)
                    if not scaf.store.has_blob(blob_id):
                        scaf.store.add_blob(blob_id,path)

                    file_dict = dict(
                        blob_id=blob_id,
                        filename=item['filename'],
                        sourcefiles=[]
                    )
                    if not deps is None:
                        for dep in deps:
                            with open(dep,'rb') as fid:
                                dep_id = calculate_blob_checksum(fid)
                            if not scaf.store.has_blob(dep_id):
                                scaf.store.add_blob(dep_id,dep)
                            file_dict["sourcefiles"].append(dict(
                                blob_id=dep_id,
                                filename=basename(dep)
                            ))

                    out['files'][id] = file_dict

            for obj_type in ["parts","tools","results"]:
                if obj_type in openscad:
                    for id,item in openscad[obj_type].iteritems():
                        obj_dict = {}
                        obj_dict["name"] = item.pop('name')
                        if "description" in item:
                            obj_dict["description"] = item.pop('description')

                        quantity = item.pop('quantity',1)
                        optional = item.pop('optional',False)

                        #create image
                        path, deps = scaf.cache.process(
                            self._image,
                            importer='openscad',
                            extension='.png',
                            **item)
                        with open(path,'rb') as fid:
                            blob_id = calculate_blob_checksum(fid)
                        if not scaf.store.has_blob(blob_id):
                            scaf.store.add_blob(blob_id,path)

                        img_dict = dict(
                            blob_id=blob_id,
                            extension='.png',
                            alt="Render of %s" % obj_dict["name"],
                            sourcefiles=[]
                        )
                        if not deps is None:
                            for dep in deps:
                                with open(dep,'rb') as fid:
                                    dep_id = calculate_blob_checksum(fid)
                                if not scaf.store.has_blob(dep_id):
                                    scaf.store.add_blob(dep_id,dep)
                                img_dict["sourcefiles"].append(dict(
                                    blob_id=dep_id,
                                    filename=basename(dep)
                                ))

                        obj_dict["images"] = [img_dict]

                        obj_id = common.Object.calculate_checksum(**obj_dict)

                        if not scaf.store.has_obj(obj_id):
                            scaf.store.add_obj(common.Object(
                                obj_id=obj_id,
                                **obj_dict
                            ))

                        if obj_type == "results":
                            out[obj_type][id] = dict(
                                obj_id=obj_id,
                                created=True,
                                quantity=quantity
                            )
                        else:
                            out[obj_type][id] = dict(
                                obj_id=obj_id,
                                optional=optional,
                                quantity=quantity
                            )
