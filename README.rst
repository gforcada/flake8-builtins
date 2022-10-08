.. -*- coding: utf-8 -*-

.. image:: https://github.com/gforcada/flake8-builtins/actions/workflows/testing.yml/badge.svg?event=push
   :target: https://github.com/gforcada/flake8-builtins/actions/workflows/testing.yml

.. image:: https://coveralls.io/repos/gforcada/flake8-builtins/badge.svg?branch=master
   :target: https://coveralls.io/github/gforcada/flake8-builtins?branch=master

Flake8 Builtins plugin
======================
Check for python builtins being used as variables or parameters.

Imagine some code like this:

.. code:: Python

    def max_values(list, list2):
        max = list[0]
        for x in list:
            if x > 0:
                max = x

        all_values = list()
        all_values.append(max)

        max = list2[0]
        for x in list2:
            if x > 0:
                max = x
        all_values.append(max)

        return all_values

    max_values([3, 4, 5, ], [5, 6, 7])

The last statement is not returning ``[5, 7]`` as one would expect,
instead is raising this exception::

    Traceback (most recent call last):
      File "test.py", line 17, in <module>
        max_values([3,4,5], [4,5,6])
      File "bla.py", line 6, in max_values
        all_values = list()
    TypeError: 'list' object is not callable

**Why?** Because ``max_value`` function's first argument is ``list`` a Python builtin.
Python allows to override them, but although could be useful in some really specific use cases,
the general approach is to **not** do that as code then can suddenly break without a clear trace.

Example
-------
Given the following code:

.. code:: Python

    def my_method(object, list, dict):
        max = 5
        min = 3
        zip = (4, 3)

The following warnings are shown (via flake8)::

   test.py:1:15: A002 argument "object" is shadowing a python builtin
   test.py:1:23: A002 argument "list" is shadowing a python builtin
   test.py:1:29: A002 argument "dict" is shadowing a python builtin
   test.py:2:5: A001 variable "max" is shadowing a python builtin
   test.py:3:5: A001 variable "min" is shadowing a python builtin
   test.py:4:5: A001 variable "zip" is shadowing a python builtin

Install
-------
Install with pip::

    $ pip install flake8-builtins

Options
-------

One can use `--builtins-ignorelist` option, or configuration option,
to ignore a custom list of builtins::

    $ flake8 --builtins-ignorelist id,copyright *.py

Requirements
------------
- Python 3.7, 3.8, 3.9
- flake8

License
-------
GPL 2.0
