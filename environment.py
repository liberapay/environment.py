"""This library provides parsing and validation of environment variables.


Installation
------------

:py:mod:`environment` is available on `GitHub`_ and on `PyPI`_::

    $ pip install environment

We `test <https://travis-ci.org/gittip/environment.py>`_ against
Python 2.6, 2.7, 3.2, and 3.3.

:py:mod:`environment` is MIT-licensed.


.. _GitHub: https://github.com/gittip/environment.py
.. _PyPI: https://pypi.python.org/pypi/environment


Tutorial
--------

First let's pretend that this is our ``os.environ``:

>>> pretend_os_environ = { 'FOO': '42'
...                      , 'BAR_BAZ': 'buz'
...                      , 'BAR_BLOO_BLOO': 'yes'
...                      , 'BAD': 'to the bone'
...                       }

The way the :py:mod:`environment` library works is you instantiate an
:py:class:`Environment` class like so:

>>> from environment import Environment, is_yesish
>>> env = Environment( FOO=int
...                  , BAR_BAZ=None
...                  , BAR_BLOO_BLOO=is_yesish
...                  , BLAH=None
...                  , BAD=int
...                  , _environ=pretend_os_environ
...                   )

Keyword arguments (besides ``_environ``, which is special-cased) specify which
variables to look for and how to typecast them. A type of ``None`` will
result in a value of type :py:class:`str` (:py:class:`unicode` under Python 2).
Since a process environment contains a lot of crap you don't care about, we
only parse out variables that you explicitly specify in the keyword arguments.

The resulting object has lowercase attributes for all variables that were asked
for and found:

>>> env.foo
42

We support one level of namespacing:

>>> env.bar.baz
'buz'
>>> env.bar.bloo_bloo
True

There are also :py:attr:`~Environment.missing` and
:py:attr:`~Environment.malformed` attributes for variables that weren't found
or couldn't be typecast:

>>> env.missing
['BLAH']
>>> env.malformed
{'BAD': "ValueError: invalid literal for int() with base 10: 'to the bone'"}

You're expected to inspect the contents of :py:attr:`~Environment.missing` and
:py:attr:`~Environment.malformed` and do your own error reporting.


API Reference
-------------

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys


__version__ = '0.0.0-dev'


class Environment(object):
    """This class represents a subset of a process environment.

    :param spec: Keyword arguments are of the form ``VARIABLE_NAME=type``. If
        ``type`` is None then the value will be stored as :py:class:`str`
        (:py:class:`unicode` under Python 2).

    :param mapping _environ: By default of course we look at
        :py:attr:`os.environ`, but you can override that with this, which can
        only be given as a keyword argument. We operate on a shallow copy of this
        mapping (though if all values are strings, it's effectively a deep copy,
        since strings are immutable).

    The constructor for this class loops through the items in ``_environ``,
    skipping those variables not also named in ``spec``, and parsing those that
    are. We store variables using lowercased names.

    If a variable is mentioned in ``spec`` but is not in ``_environ``, the
    variable name is recorded in the :py:attr:`missing` list. If typecasting a
    variable raises an exception, the variable name and an error message are
    recorded in the :py:attr:`malformed` dictionary.

    If a variable name includes an underscore (``_``), then the first part of
    the name is taken to be a namespace, and all variables beginning with that
    part are collected under an :py:class:`EnvironmentVariableGroup` instance.
    The rest of the name is the attribute name. So ``MYAPP_VARIABLE_NAME``
    would end up at ``env.myapp.variable_name``. We only support one level of
    namespacing, and malformed variables don't generate namespaces.

    """

    missing = []    #: A list of variable names that are in ``spec`` but not ``_environ``.
    malformed = {}  #: A dictionary of error messages for typecasting failures, keyed by variable name.

    def __init__(self, **spec):
        environ = spec.pop('_environ', os.environ)

        # We're going to mutate environ, so let's work with a copy. It can be a
        # shallow copy since the values are all strings (which are immutable, so
        # copying them over at all is effectively a deep copy).
        environ = environ.copy()

        self.missing = sorted(list(set(spec) - set(environ)))
        self.malformed = {}

        for name, value in sorted(environ.items()):

            # Skip envvars we don't care about.
            if name not in spec:
                continue

            # Ensure we have a string.
            if sys.version_info < (3, 0, 0):
                encoding = sys.getfilesystemencoding()
                value = value.decode(encoding)

            # Decide how to typecast.
            type_ = spec[name]
            if type_ is None:
                type_ = lambda o: o

            # Typecast!
            try:
                value = type_(value)
            except:
                exc_type, exc_instance = sys.exc_info()[:2]
                msg = "{}: {}".format(exc_type.__name__, exc_instance)
                self.malformed[name] = msg
                continue

            # Pick an object and attribute name.
            parts = name.split('_')
            first = parts[0]
            obj = self
            attr = name
            if len(parts) > 1:
                section = first.lower()
                if section not in self.__dict__:
                    # Create a new section if need be.
                    self.__dict__[section] = EnvironmentVariableGroup()
                obj = self.__dict__[section]
                attr = '_'.join(parts[1:])
            attr = attr.lower()

            # Store the value.
            obj.__dict__[attr] = value


class EnvironmentVariableGroup(object):
    """Instantiated by :py:class:`Environment` to represent groups of environment variables.
    """


def is_yesish(value):
    """Typecase booleanish environment variables to :py:class:`bool`.

    :param string value: An environment variable value.

    :return bool: Return :py:class:`True` if ``value`` is ``1``, ``true``, or
        ``yes`` (case-insensitive), and :py:class:`False` otherwise.

    """
    return value.lower() in ('1', 'true', 'yes')


if __name__ == '__main__':
    import doctest
    doctest.testmod()
