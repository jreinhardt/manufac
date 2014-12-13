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

"""
This module defines "proces verbal" a simple domain specific language for
writing assembly instructions in semistructured natural language.
"""
from pyparsing import Or, CaselessLiteral, OneOrMore, Word, printables, replaceWith, nums, Optional, CaselessKeyword,NotAny, Group, alphanums, ZeroOrMore, Literal, Combine
import pyparsing
from os.path import join,dirname, exists, basename, splitext

from manuallabour.core.common import Object, Step, calculate_blob_checksum
from manuallabour.core.graph import Graph
id_end = []

number_digits = Word(nums).setParseAction(lambda t: int(t[0]))
number_phrase = Or([
    CaselessLiteral(l).setParseAction(replaceWith(v)) for l,v in [
        ("a",1),
        ("one",1),
        ("a pair",2),
        ("two",2),
        ("three",3),
        ("four",4),
        ("five",5)]
    ])
number = Or((number_digits,number_phrase))

verb = Or([CaselessKeyword(v) for v in [
    'add',
    'put',
    'push',
    'slide',
    'attach',
    'screw',
    'bolt',
    'place',
    'paint',
    'sand',
    'insert',
    'clip',
    'tighten',
    'fix']])

preposition = Or([CaselessKeyword(p).suppress() for p in [
    "into",
    "to",
    "on",
    "through",
    "onto"]])
id_end.append(preposition)

the = CaselessKeyword("the").suppress()
id_end.append(the)
of = CaselessKeyword("of").suppress()
id_end.append(of)

using = Or([
    CaselessKeyword("using"),
    CaselessKeyword("with")
    ]).suppress()
id_end.append(using)

depictedby = Or([
    CaselessKeyword("as shown in"),
    CaselessKeyword("shown in"),
    CaselessKeyword("see")
    ]).suppress()
id_end.append(depictedby)

assign = Or([
    CaselessKeyword("to form"),
    CaselessKeyword("to finish"),
    CaselessKeyword("to create")
    ]).suppress()
id_end.append(assign)

delim = CaselessKeyword("and").suppress()
id_end.append(delim)

id_end+=[Literal("("),Literal("(")]

pronouns = ["that","these","this"]
pronoun = Or([CaselessKeyword(r) for r in pronouns])

ifragment = NotAny(Or(id_end)) + Word(printables)
identifier = Combine(OneOrMore(ifragment),joinString=" ",adjacent=False)

filename = Word(alphanums + "._/")

imageref = Group(Literal("(").suppress()+depictedby+filename+Literal(")").suppress())
thing = Group(number + identifier + Optional(imageref,default=None))
reference = the + identifier
implicit = pronoun

obj = Or([thing,reference,implicit])
objlist = Group(obj + ZeroOrMore(delim + obj))

qualification = the + identifier + of
target = obj

subject = objlist

tooling = using + objlist
illustration = Group(depictedby + filename)
assignment = Group(assign + number + identifier + Optional(imageref,default=None))

verse = verb + subject + preposition + Optional(qualification,default=None) + target + Optional(tooling,default=None) + Optional(illustration,default=None) + Optional(assignment,default=None)

def _image(path,store,alt):
    with open(path,'rb') as fid:
        blob_id = calculate_blob_checksum(fid)
    if not store.has_blob(blob_id):
        store.add_blob(blob_id,path)
    return dict(
        blob_id=blob_id,
        extension=splitext(path)[1],
        alt=alt
        )

def _object(parsed,store,basedir,created=False):
    quantity, name, img = parsed
    obj = dict(name=name)
    if not img is None:
        obj["images"] = [_image(
            join(basedir,img[0]),
            store,
            "Illustration of %s" % name
        )]

    obj_id = Object.calculate_checksum(**obj)
    if not store.has_obj(obj_id):
        store.add_obj(Object(obj_id=obj_id,**obj))

    return dict(
        obj_id=obj_id,
        quantity=quantity,
        created=created
    )

def load_graph(input_file,store,basedir):
    steps = []
    results = {}
    for line in open(input_file):
        verb, subjects,_,target,tools,image,assign = verse.parseString(line)
        step = {}
        step["title"] = "%s %s" % (verb.capitalize(),subjects[0][1])
        if image is None:
            step["description"] = line
        else:
            step["description"] = line.replace(image[0],"the picture") + \
                "\n{{image(img)}}\n"
        step["parts"] = {}

        obj_index = 0
        for subject in subjects:
            if isinstance(subject,pyparsing.ParseResults):
                #Object description
                step["parts"]["p%d" % obj_index] = _object(subject,store,basedir)
            else:
                if subject in pronouns:
                    prev_step = store.get_step(steps[-1]["step_id"])
                    step["parts"]["p%d" % obj_index] = dict(
                        obj_id = prev_step.results["result"].obj_id,
                        quantity = prev_step.results["result"].quantity
                    )
                else:
                    #Object reference
                    step["parts"]["p%d" % obj_index] = dict(
                        obj_id=results[subject]
                    )
            obj_index += 1

        #target
        if isinstance(target,pyparsing.ParseResults):
            #Object description
            step["parts"]["target"] = _object(target,store,basedir)
        else:
            if target in pronouns:
                prev_step = store.get_step(steps[-1]["step_id"])
                if "target" in step["parts"]:
                    step["parts"]["target"] = dict(
                        obj_id = prev_step.results["result"].obj_id,
                        quantity = prev_step.results["result"].quantity
                    )
            else:
                #Object reference
                step["parts"]["target"] = dict(obj_id=results[target])

        #tools
        if not tools is None:
            step["tools"] = {}
            for tool in tools:
                if isinstance(tool,pyparsing.ParseResults):
                    #Object description
                #Object description
                    step["tools"]["t%d" % obj_index] = _object(tool,store,basedir)
                else:
                    if tool in pronouns:
                        prev_step = store.get_step(steps[-1]["step_id"])
                        step["tools"]["t%d" % obj_index] = dict(
                            obj_id = prev_step.results["result"].obj_id,
                            quantity = prev_step.results["result"].quantity
                        )
                    else:
                        #Object reference
                        step["tools"]["t%d" % obj_index] = dict(
                            obj_id=results[tool]
                        )
                obj_index += 1
        #image
        if not image is None:
            step["images"] = dict(img=_image(
                join(basedir,image[0]),
                store,
                "Illustration of this step"
                )
            )

        #result
        if not assign is None:
            res = _object(assign,store,basedir,created=True)
            step["results"] = dict(result=res)
            results[assign[1]] = res["obj_id"]

        step_id = Step.calculate_checksum(**step)
        if not store.has_step(step_id):
            store.add_step(Step(step_id=step_id,**step))

        if len(steps) == 0:
            step_ref = dict(step_id=step_id)
        else:
            step_ref = dict(step_id=step_id,requires=[steps[-1]["step_id"]])
        steps.append(step_ref)

    graph_id = Graph.calculate_checksum(steps=steps)
    return Graph(graph_id=graph_id,steps=steps)

