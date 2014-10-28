import unittest
import json
from os import makedirs, utime
from shutil import rmtree
from codecs import open
from time import sleep

from manuallabour.cl.utils import *

class CallCounter:
    def __init__(self,callback):
        self.call_count = 0
        self.last_args = None
        self.last_kwargs = None
        self.callback = callback
    def __call__(self,*args,**kwargs):
        self.call_count += 1
        self.last_args = args
        self.last_kwargs = kwargs
        return self.callback(*args,**kwargs)

def mock_callback(fn,**kwargs):
    open(fn,'w','utf8').close()
    return ['tests/cache/test/dep1']

def retry_callback(fn,**kwargs):
    open(fn,'w','utf8').close()
    return None

class CacheTest(unittest.TestCase):
    def test_cold_start(self):
        rmtree('tests/cache/cold',True)
        makedirs('tests/cache/cold')
        with FileCache('tests/cache/cold') as fc:
            self.assertEqual(fc.dependencies,{})

    def test_hot_start(self):
        rmtree('tests/cache/hot',True)
        makedirs('tests/cache/hot')
        with open('tests/cache/hot/.deps','w','utf8') as fid:
            fid.write(json.dumps({}))
        with FileCache('tests/cache/cold') as fc:
            pass

    def test_caching(self):
        rmtree('tests/cache/test',True)
        makedirs('tests/cache/test')

        #dependencies
        with FileCache('tests/cache/test') as fc:
            #create a dependency
            open('tests/cache/test/dep1','w','utf8').close()
            callback = CallCounter(mock_callback)

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,1)

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,1)

            #Make sure new mtime differs from old one
            sleep(0.1)
            utime('tests/cache/test/dep1',None)

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,2)

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,2)

        #reopen cache
        with FileCache('tests/cache/test') as fc:
            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,2)

    def test_retry(self):
        rmtree('tests/cache/retry',True)
        makedirs('tests/cache/retry')

        #dependencies
        with FileCache('tests/cache/retry') as fc:
            #create a dependency
            open('tests/cache/retry/dep1','w','utf8').close()
            callback = CallCounter(retry_callback)

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,1)

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,2)

            #Make sure new mtime differs from old one
            sleep(0.1)
            utime('tests/cache/test/dep1',None)

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,3)

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,4)

        #reopen cache
        with FileCache('tests/cache/test') as fc:
            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,5)

    def test_clear(self):
        rmtree('tests/cache/clear',True)
        makedirs('tests/cache/clear')
        with FileCache('tests/cache/clear') as fc:
            #create a dependency
            open('tests/cache/test/dep1','w','utf8').close()
            callback = CallCounter(mock_callback)

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,1)

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,1)

            fc.clear()

            fc.process(callback,importer='test',extension='.tmp',arg=4)
            self.assertEqual(callback.call_count,2)


