"""This library provides parsing and validation of environment variables.


Rationale
---------

Configuration via environment variables has become popular with the rise of
`twelve-factor apps`_, yet few Python libraries exist to help with it (despite
the abundance of libraries for command line and file configuration).

When I `looked around`_, most of the solutions I found involved using
:py:attr:`os.environ` directly, or overloading somewhat related libraries such
as :py:mod:`argparse` or :py:mod:`formencode`. The former are not robust enough
with regards to typecasting and error handling. The latter are inappropriate
and overengineered: the reason to prefer envvar configuration in the first
place is to reduce complexity, not compound it. We need something designed
specifically and solely for taking configuration from environment variables.

The one library I found is `python-decouple`_, which does indeed rationalize
typecasting of environment variables. However, it also handles file
configuration, which adds unwanted complexity and (ironically) muddying of
concerns. Additionally, it doesn't enable robust error messaging. The problem
with error handling in :py:mod:`decouple` and in ad-hoc usage of
:py:attr:`os.environ` is that if you have four environment variables wrong, you
only find out about them one at a time. We want to find out about all problems
with our configuration at once, so that we can solve them all at once instead
of playing configuration roulette ("Will it work this time? No! How about
now?").

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
...                  , environ=pretend_os_environ
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
:py:attr:`~Environment.malformed` and do your own error reporting. You're also
expected to handle defaults yourself at a higher level---this is not a
general-purpose configuration library---though the
:py:attr:`~Environment.parsed` dictionary should help with that:

>>> env.parsed
{'foo': 42}

If all of the environment variables you care about share a common prefix, you
can specify this to the constructor to save yourself some clutter:

>>> bar = Environment( 'BAR_'
...                  , BAZ=str
...                  , BLOO_BLOO=is_yesish
...                  , environ=pretend_os_environ
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


__version__ = '1.0.0'


class Environment(object):
    """Represent a whitelisted, parsed subset of a process environment.

    :param string prefix: If all of the environment variables of interest to
        you share a common prefix, you can specify that here. We will use this
        prefix when pulling values out of the environment, and the attribute
        names you end up with won't include the prefix.

    :param mapping spec: A mapping of environment variable names to typecasters.

    :param mapping environ: By default we look at :py:attr:`os.environ`, of
        course, but you can override that with this. We operate on a shallow
        copy of this mapping (though it's effectively a deep copy in the normal
        case where all values are strings, since strings are immutable).

    :param kw: Keyword arguments are folded into ``spec``.

    The constructor for this class loops through the items in ``environ``,
    skipping those variables not also named in ``spec``, and parsing those that
    are, using the ``type`` specified. Under Python 2, we harmonize with Python
    3's behavior by decoding environment variable values to :py:class:`unicode`
    using the result of :py:func:`sys.getfilesystemencoding()` before
    typecasting. The upshot is that if you want typecasting to be a
    pass-through for a particular variable, you should specify the
    Python-version-appropriate string type: :py:class:`str` for Python 3,
    :py:class:`unicode` for Python 2. We store variables using lowercased
    names, so ``MYVAR`` would end up at ``env.myvar``:

    >>> env = Environment(MYVAR=int, environ={'MYVAR': 42})
    >>> env.myvar
    42

    If a variable is mentioned in ``spec`` but is not in ``environ``, the
    variable name is recorded in the :py:attr:`missing` list. If typecasting a
    variable raises an exception, the variable name and an error message are
    recorded in the :py:attr:`malformed` list:

    >>> env = Environment(MYVAR=int, OTHER=str, environ={'MYVAR': 'blah'})
    >>> env.missing
    ['OTHER']
    >>> env.malformed
    [('MYVAR', "ValueError: invalid literal for int() with base 10: 'blah'")]

    If ``prefix`` is provided, then we'll add that to the variable names in
    ``spec`` when reading the environment:

    >>> foo = Environment('FOO_', BAR=int, environ={'FOO_BAR': '42'})
    >>> foo.prefix
    'FOO_'
    >>> foo.bar
    42

    The copy of ``environ`` that we act on is stored at
    :py:attr:`~Environment.environ`:

    >>> foo.environ
    {'FOO_BAR': '42'}

    All parsed variables are stored in the
    dictionary at :py:attr:`~Environment.parsed`:

    >>> foo.parsed
    {'bar': 42}

    Use the :py:attr:`~Environment.parsed` dictionary, for example, to fold
    configuration from the environment together with configuration from other
    sources (command line, config files, defaults) in higher-order data
    structures. Attribute access for non-class attributes on
    :py:class:`Environment` instances uses :py:attr:`~Environment.parsed`
    rather than :py:attr:`__dict__`, which means that you can set attributes on
    the instance and they're reflected in :py:attr:`~Environment.parsed`:

    >>> foo.bar = 537
    >>> foo.parsed
    {'bar': 537}

    But setting attributes doesn't modify :py:attr:`~Environment.environ`:

    >>> foo.environ
    {'FOO_BAR': '42'}

    """

    environ = {}    #: A copy of the dictionary we started with.
    parsed = {}     #: The dictionary we ended up with after parsing in the constructor.
    prefix = ''     #: The prefix in use.
    missing = []    #: A sorted list of variable names that are in ``spec`` but not ``environ``.
    malformed = []  #: A sorted list of (variable name, error message) tuples for typecasting failures.
    spec = {}       #: A mapping of environment variable names to typecasters.

    def __init__(self, prefix='', spec=None, environ=None, **kw):

        # Default to os.environ.
        _encoding = None
        if environ is None:
            environ = os.environ

            # Under Python 2, adopt Python 3 encoding semantics for os.environ.
            if sys.version_info < (3, 0, 0):
                _encoding = sys.getfilesystemencoding()

        # We're going to mutate environ, so let's work with a copy. It can be a
        # shallow copy since the values are all strings (which are immutable, so
        # copying them over at all is effectively a deep copy).
        self.environ = environ.copy()
        del environ  # Just so we don't accidentally use it below.

        if spec is None:
            spec = {}
        spec.update(kw)
        self.spec = spec
        del spec

        self.prefix = prefix
        self.missing, self.malformed, self.parsed = \
                                        self.parse(self.prefix, self.spec, self.environ, _encoding)


    @staticmethod
    def parse(prefix, spec, environ, encoding):
        """Heavy lifting, with no side-effects on ``self``.

        :param string prefix: The string to prefix to variable names when
            looking them up in ``environ``.

        :param mapping spec: A mapping of environment variable names to
            typecasters.

        :param mapping environ: A mapping of environment variable names to
            values.

        :param string encoding: The encoding with which to decode environment
            variable values before typecasting them, or :py:class:`None` to
            suppress decoding.

        :returns: A three-tuple, corresponding to
            :py:attr:`~Environment.missing`, :py:attr:`~Environment.malformed`,
            and :py:attr:`~Environment.parsed`.

        """
        missing = sorted(list(set(spec) - set(environ)))
        malformed = []
        parsed = {}

        for name, value in sorted(environ.items()):

            # Skip envvars we don't care about.
            if not name.startswith(prefix):
                continue
            unprefixed = name[len(prefix):]
            if unprefixed not in spec:
                continue

            # Ensure we have a string.
            if encoding is not None:
                value = value.decode(encoding)

            # Decide how to typecast.
            type_ = spec[unprefixed]

            # Typecast!
            try:
                value = type_(value)
            except:
                exc_type, exc_instance = sys.exc_info()[:2]
                msg = "{0}: {1}".format(exc_type.__name__, exc_instance)
                malformed.append((name, msg))
                continue

            # Store the value.
            parsed[unprefixed.lower()] = value

        return missing, malformed, parsed


    # Delegate attribute access to the self.parsed dictionary.

    def __getattr__(self, name):
        try:
            return self.parsed[name]
        except KeyError:
            cls = self.__class__.__name__
            raise AttributeError("'{0}' object has no attribute '{1}'".format(cls, name))

    def __setattr__(self, name, value):
        if name in self.__class__.__dict__:
            self.__dict__[name] = value
        else:
            self.parsed[name] = value


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
