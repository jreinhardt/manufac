# manufac - a commandline tool for step-by-step instructions
# Copyright (C) 2014 Johannes Reinhardt <jreinhardt@ist-dein-freund.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from os.path import join,dirname, exists, basename

from pkg_resources import iter_entry_points
import pkg_resources

from manufac.utils import FileCache
from manufac.importers.common import GraphScaffolding

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

