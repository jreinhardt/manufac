Quick Start
===========

As an example lets look at a simple instruction for preparing pizza. To
prepare pizza one needs to put tomato sauce onto the dough, add mushrooms,
grate some cheese over everything and put it into the preheated oven for 20
minutes.

manufac gets all the data it needs from plain text files, and it understands
different input formats. At the moment there are YAML files, which are quite
detailed and give a lot of control over the output, and pv files, which are
much more concise and very readable, but more limited.

YAML Example
------------

YAML is a format that is easy to read and write for both humans and computers. If you make a mistake in formatting your input file, manufac will usually tell you what is wrong.

The contents of `pizza.yaml` are

.. literalinclude:: pizza.yaml

Note that the order of markup is not necessarily the same as in the rendered
instructions. In the yaml file, the steps and their dependencies (in the
requires field) are described, the order in the final instructions is figured
out automatically.

In the parts section of step s2 the different markups for an associative
array are used, one can use them interchangeably to get the nicest markup.
The different markups for the `duration` and `waiting` fields are
demonstrated, which allows to write timespans in a range of intuitive
notations. In step s4 a reference to the result of step s2 is used,
indicating that the same object is used in both steps.

To let manufac process the file, use::

  manufac render pizza.yaml

This results in a folder `doc` (unless specified otherwise with the `-o`
option) with the rendered instructions in html format.

Proces-verbal example
---------------------

Proces-verbal (pv) is a input format that is very close to natural language,
and therefore very readable. On the other hand it is much less expressive and
more limited than YAML, and still in its early stages of development.

A rough equivalent of the instruction above would look like this

.. literalinclude:: pizza.pv

Note that in contrast to YAML, the order is much more important, as manufacs
ability to detect dependencies between the steps is very limited.

Rendering works just like with YAML::

  manufac render pizza.pv

This results in a folder `doc` (unless specified otherwise with the `-o`
option) with the rendered instructions in html format.
