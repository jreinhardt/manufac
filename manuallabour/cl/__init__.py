import argparse
import sys
from os.path import join,dirname

from manuallabour.cl import yaml_reader

def main_function():
    parser = argparse.ArgumentParser(description="Tool for rendering beautiful step-by-step instructions")
    parser.add_argument('input',help='input ml file',type=str)
    parser.add_argument('-o',help='output directory',dest='output',type=str,default='docs')
    parser.add_argument('-f',help='export format',dest='format',type=str,choices=['html','text'],default='html')
    parser.add_argument('-l',help='layout (for html only)',dest='layout',type=str,choices=['deck','bootstrap'],default='deck')

    args = vars(parser.parse_args())

    g = yaml_reader.graph_from_YAML(args['input'])

