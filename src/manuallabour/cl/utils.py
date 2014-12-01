import json
import hashlib
from os.path import join, exists
from os import lstat, utime, makedirs
from codecs import open
from shutil import rmtree

class FileCache:
    """
    Context manager to allow caching
    """
    def __init__(self,path):
        self.path = path
        self.dependencies = None
    def __enter__(self):
        #load cached dependency data
        dep_path = join(self.path,'.deps')
        if not exists(dep_path):
            self.dependencies = {}
        else:
            with open(dep_path,'r','utf8') as fid:
                self.dependencies = json.loads(fid.read())
        return self

    def __exit__(self,exc_type,exc_val,exc_tb):
        #write dependency data
        with open(join(self.path,'.deps'),'w','utf8') as fid:
            fid.write(json.dumps(self.dependencies))
            self.dependencies = None
        return False

    def clear(self):
        """
        Clear the cache and all files in it
        """
        rmtree(self.path)
        makedirs(self.path)
        self.dependencies = {}

    def process(self,callback,**kwargs):
        """
        calls the callable callback to create a file and returns its path.
        the callback must return a list of file paths the created file
        depends on and which make reexecution of the callback necessary if
        modified. Alternatively None can be returned to retry 
        additional keyword arguments can be used to supply any information to
        callback and dependencies. An id of the calling importer is required
        and an extension for the resulting file is required.

        callback(target_filename,importer='imp_id',extension='.png',**kwargs)
        """
        assert 'importer' in kwargs
        assert 'extension' in kwargs

        #calculate target file id
        m = hashlib.sha512()
        for k in sorted(kwargs.keys()):
            m.update(k)
            m.update(str(kwargs[k]))

        target_id = m.hexdigest()

        #check if update is nessecary
        update = False

        target_path = join(self.path,target_id + kwargs["extension"])

        if not exists(target_path):
#            print "Target path for %s does not exist" % target_id
            update = True
        elif not target_id in self.dependencies:
#            print "Dependencies for %s do not exist" % target_id
            update = True
        elif self.dependencies[target_id] is None:
            #The callback requested to try again next time
            update = True
        else:
            target_time = lstat(target_path).st_mtime
            for dep in self.dependencies[target_id]:
                if not exists(dep):
#                    print "Dependency %s for %s does not exist" % (dep,target_id)
                    update = True
                    break
                elif lstat(dep).st_mtime > target_time:
#                    print "Dependency %s for %s is outdated" % (dep,target_id)
#                    print target_time, lstat(dep).st_mtime
                    update = True
                    break

        if update:
#            print "Updating %s" % target_id
            self.dependencies[target_id] = callback(target_path,**kwargs)
            utime(target_path,None)

        return target_path, self.dependencies[target_id]
