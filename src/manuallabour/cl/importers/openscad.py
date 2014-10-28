from manuallabour.cl.importers.common import ImporterBase
from tempfile import mkstemp
from subprocess import call
import os
import hashlib
from os.path import basename, splitext

import manuallabour.core.common as common

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

    def process(self,step_id,in_dict,out_dict,reqs,store,cache):
        step_dict = in_dict["steps"][step_id]
        if not 'openscad' in step_dict:
            return

        if "images" in step_dict["openscad"]:
            for id,item in step_dict["openscad"]["images"].iteritems():
                path = cache.process(
                    self._image,
                    importer='openscad',
                    extension='.png',
                    **item)
                res_id = splitext(basename(path))[0]

                store.add_res(
                    common.Image(
                        res_id,
                        extension='.png',
                        alt='Render of %s' % item['scadfile']
                    ),
                    path
                )

                out_dict[step_id]['images'][id] = \
                    common.ResourceReference(res_id)

        if "files" in step_dict["openscad"]:
            for id,item in step_dict["openscad"]["files"].iteritems():
                path = cache.process(
                    self._file,
                    importer='openscad',
                    extension=splitext(item['filename'])[1],
                    **item)
                res_id = splitext(basename(path))[0]

                store.add_res(
                    common.File(
                        res_id,
                        filename=item['filename']
                    ),
                    path
                )

                out_dict[step_id]['files'][id] = \
                    common.ResourceReference(res_id)

        for obj_type in ["parts","tools","results"]:
            if obj_type in step_dict["openscad"]:
                for id,item in step_dict["openscad"][obj_type].iteritems():

                    obj_name = item.pop('name')
                    obj_description = item.pop('description','')

                    quantity = item.pop('quantity',1)
                    optional = item.pop('optional',False)

                    # calculate obj id
                    m = hashlib.sha512()
                    m.update(obj_name)
                    m.update(obj_description)
                    obj_id = m.hexdigest()

                    path = cache.process(
                        self._image,
                        importer='openscad',
                        extension='.png',
                        **item)
                    res_id = splitext(basename(path))[0]

                    if not store.has_res(res_id):
                        store.add_res(
                            common.Image(
                                res_id,
                                extension='.png',
                                alt=obj_name
                            ),
                            path
                        )


                    if not store.has_obj(obj_id):
                        store.add_obj(common.Object(
                            obj_id,
                            name=obj_name,
                            images=[common.ResourceReference(res_id)]
                        ))

                    if obj_type == "results":
                        out_dict[step_id][obj_type][id] = common.ObjectReference(
                            obj_id,
                            created=True,
                            quantity=quantity
                        )
                    else:
                        out_dict[step_id][obj_type][id] = common.ObjectReference(
                            obj_id,
                            optional=optional,
                            quantity=quantity
                        )
