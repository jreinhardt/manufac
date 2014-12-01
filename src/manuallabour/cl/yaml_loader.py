from os.path import join,dirname, exists, basename

from pkg_resources import iter_entry_points
import pkg_resources

from manuallabour.cl.utils import FileCache
from manuallabour.cl.importers.common import GraphScaffolding

def load_graph(input_file,store):
    importers = []
    basedir = dirname(input_file)
    for ep in iter_entry_points('importers'):
        importers.append(ep.load()(basedir))

    cachedir = join(basedir,'.mlcache')
    if not exists(cachedir):
        makedirs(cachedir)

    scaf = GraphScaffolding(input_file,store,FileCache(cachedir),importers)

    return scaf.get_graph()

