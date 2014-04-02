"""This library provides parsing and validation of environment variables.


Rationale
---------

Configuration via environment variables has become popular with the rise of
`twelve-factor apps`_, yet few Python libraries exist to help with it (despite
the abundance of libraries for command line and file configuration).

When I `looked around`_, most of the solutions I found involved using
:py:attr:`os.environ` directly, or making clever use of :py:mod:`argparse` or
:py:mod:`formencode`. The former are not robust enough with regards to
typecasting and error handling.  The latter are inappropriate and
overengineered: the reason to prefer envvar configuration in the first place is
to reduce complexity, not compound it. We need something designed specifically
and solely for configuration via environment variables.

The one library I found is `python-decouple`_, which does indeed rationalize
typecasting of environment variables. However, it also handles file
configuration, which adds unwanted complexity and muddying of concerns, and it
doesn't enable robust error messaging. The problem with error handling in
:py:mod:`decouple` and in ad-hoc usage of :py:attr:`os.environ` is that if you
have four environment variables wrong, you only find out about them one at a
time. We want to find out about all problems with our configuration at once, so
that we can solve them all at once instead of playing configuration roulette
("Will it work this time? No! How about now?").

This present library is designed to be small in scope, limited to environment
variables only, and to support robust error messaging. Look into `foreman`_ and
`honcho`_ for process management tools to complement this library.

.. _twelve-factor apps: http://12factor.net/config
.. _looked around: https://twitter.com/whit537/status/450780504921755648
.. _python-decouple: https://pypi.python.org/pypi/python-decouple
.. _foreman: http://ddollar.github.io/foreman/
.. _honcho: http://honcho.readthedocs.org/en/latest/


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

And let's import our stuff:

>>> from environment import Environment, is_yesish

The way the :py:mod:`environment` library works is you instantiate an
:py:class:`Environment` class like so:

>>> env = Environment( FOO=int
...                  , BLAH=str
...                  , BAD=int
...                  , _environ=pretend_os_environ
...                   )

Keyword arguments specify which variables to look for and how to typecast them.
Since a process environment contains a lot of crap you don't care about, we
only parse out variables that you explicitly specify in the keyword arguments.

The resulting object has lowercase attributes for all variables that were asked
for and found:

>>> env.foo
42

There are also :py:attr:`~Environment.missing` and
:py:attr:`~Environment.malformed` attributes for variables that weren't found
or couldn't be typecast:

>>> env.missing
['BLAH']
>>> env.malformed
[('BAD', "ValueError: invalid literal for int() with base 10: 'to the bone'")]

You're expected to inspect the contents of :py:attr:`~Environment.missing` and
:py:attr:`~Environment.malformed` and do your own error reporting.

If all of the environment variables you care about share a common prefix, you
can specify this to the constructor to save yourself some clutter:

>>> bar = Environment( 'BAR_'
...                  , BAZ=str
...                  , BLOO_BLOO=is_yesish
...                  , _environ=pretend_os_environ
...                   )
>>> bar.baz
'buz'
>>> bar.bloo_bloo
True


API Reference
-------------

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys


__version__ = '0.0.0-dev'


class Environment(object):
    """This class represents a subset of a process environment.

    :param string prefix: If all of the environment variables of interest to
        you share a common prefix, you can specify that here. We will use that
        prefix when pulling values out of the environment, and the attribute
        names you end up with won't include the prefix.

    :param spec: Keyword arguments are of the form ``VARIABLE_NAME=type``,
        where ``VARIABLE_NAME`` is an environment variable name, and ``type``
        is a typecasting callable.

    :param mapping _environ: By default we look at :py:attr:`os.environ`, of
        course, but you can override that with this, which can only be given as
        a keyword argument. We operate on a shallow copy of this mapping
        (though it's effectively a deep copy in the normal case where all
        values are strings, since strings are immutable).

    The constructor for this class loops through the items in ``_environ``,
    skipping those variables not also named in ``spec``, and parsing those that
    are, using the ``type`` specified. Under Python 2, we harmonize with Python
    3's behavior by decoding environment variable values to :py:class:`unicode`
    using the result of :py:func:`sys.getfilesystemencoding()` before
    typecasting. The upshot is that if you want typecasting to be a pass
    through for a particular variable, you should specify the
    Python-version-appropriate string type (:py:class:`str` for Python 3,
    :py:class:`unicode` for Python 2). We store variables using lowercased
    names, so ``MYVAR`` would end up at ``env.myvar``.

    If a variable is mentioned in ``spec`` but is not in ``_environ``, the
    variable name is recorded in the :py:attr:`missing` list. If typecasting a
    variable raises an exception, the variable name and an error message are
    recorded in the :py:attr:`malformed` list.

    If ``_prefix`` is provided, then we'll use add that to the variable names
    in ``spec`` when reading the environment:

    >>> env = Environment('FOO_', BAR=int, _environ={'FOO_BAR': '42'})
    >>> env.prefix
    'FOO_'
    >>> env.bar
    42

    """

    environ = {}    #: The dictionary parsed by the constructor.
    prefix = ''     #: The prefix in use.
    missing = []    #: A sorted list of variable names that are in ``spec`` but not ``_environ``.
    malformed = []  #: A sorted list of (variable name, error message) tuples for typecasting failures.

    def __init__(self, prefix='', **spec):

        # Default to os.environ.
        decode_values_first = False
        if '_environ' in spec:
            _environ = spec.pop('_environ')
        else:
            _environ = os.environ

            # Under Python 2, adopt Python 3 encoding semantics for os.environ.
            decode_values_first = sys.version_info < (3, 0, 0)
            encoding = sys.getfilesystemencoding()

        # We're going to mutate environ, so let's work with a copy. It can be a
        # shallow copy since the values are all strings (which are immutable, so
        # copying them over at all is effectively a deep copy).
        self.environ = _environ.copy()

        self.prefix = prefix
        self.missing = sorted(list(set(spec) - set(self.environ)))
        self.malformed = []

        for name, value in sorted(self.environ.items()):

            # Skip envvars we don't care about.
            if not name.startswith(self.prefix):
                continue
            unprefixed = name[len(self.prefix):]
            if unprefixed not in spec:
                continue

            # Ensure we have a string.
            if decode_values_first:
                value = value.decode(encoding)

            # Decide how to typecast.
            type_ = spec[unprefixed]

            # Typecast!
            try:
                value = type_(value)
            except:
                exc_type, exc_instance = sys.exc_info()[:2]
                msg = "{0}: {1}".format(exc_type.__name__, exc_instance)
                self.malformed.append((name, msg))
                continue

            # Store the value.
            self.__dict__[unprefixed.lower()] = value


def is_yesish(value):
    """Typecast booleanish environment variables to :py:class:`bool`.

    :param string value: An environment variable value.

    :returns: :py:class:`True` if ``value`` is ``1``, ``true``, or ``yes``
        (case-insensitive); :py:class:`False` otherwise.

    """
    return value.lower() in ('1', 'true', 'yes')


if __name__ == '__main__':
    import doctest
    doctest.testmod()
