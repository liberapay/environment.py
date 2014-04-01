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

>>> pretend_os_environ = {'FOO': '42', 'BAR_BAZ': 'buz', 'BAR_BLOO': 'yes'}

The way this library works is you instantiate an :py:class:`Environment` class
like so:

>>> from environment import Environment, is_yesish
>>> env = Environment( 'FOO', 'BAR_'
...                  , FOO=int, BAR_BLOO=is_yesish
...                  , environ=pretend_os_environ
...                   )
>>> env.foo
42
>>> env.bar.baz
'buz'
>>> env.bar.bloo
True

Args are whitelisted environment variable names. If you tack on underscore then
any environment variables beginning with ``BAR_`` will be allowed, and they'll
be stored on a subobject.

Keyword args are typecasters for each variable (``environ`` is special-cased to
allow you to override the default, which is of course to use ``os.environ``).

So here's what the above produces:



API Reference
-------------

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys


__version__ = '0.0.0-dev'


class Section(object):
    pass


class Environment(object):
    """This class represents a process environment.

    """

    def __init__(self, *whitelist, **spec):
        environ = spec.pop('environ', os.environ)

        # We're going to mutate environ, so let's work with a copy. It can be a
        # shallow copy since the values are all strings.
        environ = environ.copy()

        # Parse prefixes out of whitelist.
        whitelist = set(whitelist)
        prefixes = set()
        for name in whitelist:
            if name.endswith('_'):
                prefix = name[:-1]
                prefixes.add(prefix)
                self.__dict__[prefix.lower()] = Section()

        # Filter out keys that aren't whitelisted.
        for name in set(environ):
            parts = name.split('_')
            first = parts[0]
            if len(parts) == 1:
                if first not in whitelist:
                    environ.pop(name)
            elif first not in prefixes:
                environ.pop(name)

        self.missing_keys = set(spec) - set(environ)
        self.extra_keys = set(environ) - set(spec)
        self.malformed_values = {}

        for name, value in environ.items():
            parts = name.split('_')

            # Pick an object and attribute name.
            obj, attr = self, name
            if len(parts) > 1:
                obj = self.__dict__[parts[0].lower()]
                attr = '_'.join(parts[1:])
            attr = attr.lower()

            # Decide how to typecast.
            cast = spec.get(name)
            if cast is None:
                cast = lambda o: o

            # Ensure we have a string.
            if sys.version_info < (3, 0, 0):
                encoding = sys.getfilesystemencoding()
                value = value.decode(encoding)

            try:
                value = cast(value)
            except:
                err = str(sys.exc_info()[1])
                self.malformed_values[name] = err

            obj.__dict__[attr.lower()] = cast(value)


def is_yesish(value):
    return value.lower() in ('1', 'true', 'yes')


if __name__ == '__main__':
    import doctest
    doctest.testmod()
