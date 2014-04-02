from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import pytest
from environment import Environment, is_yesish


if sys.version_info < (3, 0, 0):
    str_type = unicode
else:
    str_type = str


def test_Environment_basically_works():
    env = Environment(FOO_BAR=str_type, environ={'FOO_BAR': 'baz'})
    assert env.foo_bar == 'baz'
    assert env.missing == []
    assert env.malformed == []

def test_Environment_unprefixed_works():
    env = Environment(FOO=str_type, environ={'FOO': 'baz'})
    assert env.foo == 'baz'

def test_Environment_missing_is_missing():
    env = Environment(FOO=str_type, environ={})
    assert env.missing == ['FOO']

def test_Environment_malformed_is_malformed():
    env = Environment(FOO=int, environ={'FOO': 'baz'})
    assert env.malformed == [('FOO', "ValueError: invalid literal for int() with base 10: 'baz'")]

def test_Environment_extra_is_ignored():
    env = Environment(FOO=str_type, environ={'FOO_BAR_BAZ': '42'})
    assert env.missing == ['FOO']

    expected = ['environ', 'malformed', 'missing', 'parsed', 'prefix', 'spec']
    assert sorted(env.__dict__.keys()) == expected

def test_Environment_typecasting_works():
    env = Environment(FOO=int, environ={'FOO': '42'})
    assert env.foo == 42

def test_Environment_complex_typecasting_works():
    class MyType(object):
        def __init__(self, val):
            self.val = 'cheese'
    env = Environment(FOO=MyType, environ={'FOO': '42'})
    assert env.foo.val == 'cheese'

def test_Environment_prefixing_works():
    env = Environment('FOO_', BAR=str_type, environ={'FOO_BAR': '42'})
    assert env.bar == '42'

def test_Environment_prefixing_works_arbitrarily():
    env = Environment('FOO_BA', R_BAZ=int, environ={'FOO_BAR_BAZ': '42'})
    assert env.r_baz == 42

def test_Environment_can_work_with_envvars_named_prefix_and_environ():
    env = Environment( spec={'prefix': str_type, 'environ': str_type}
                     , environ={'prefix': 'and', 'environ': 'how'}
                      )
    assert env.prefix == ''
    assert env.parsed ['prefix'] == 'and'
    assert sorted(env.environ.values()) == ['and', 'how']
    assert env.parsed['environ'] == 'how'


def test_Environment_setattr_stores_attr_in_parsed():
    env = Environment()
    env.blah = 'bloo'
    assert env.parsed == {'blah': 'bloo'}

def test_Environment_setattr_stores_class_attrs_in___dict__():
    env = Environment()
    env.missing = 'bloo'
    assert env.parsed == {}
    assert env.__dict__['missing'] == 'bloo'

def test_Environment_getattr_gets_attr_from_parsed():
    env = Environment()
    env.parsed['blah'] = 'bloo'
    assert env.blah == 'bloo'

def test_Environment_getattr_raises_AttributeError():
    env = Environment()
    err = pytest.raises(AttributeError, lambda: env.blah)
    expected = "AttributeError: 'Environment' object has no attribute 'blah'"
    # Python 2 doesn't include the filename and line number in the str.
    assert str_type(err)[-len(expected):] == expected


def test_is_yesish_1_is_True():
    assert is_yesish('1')

def test_is_yesish_true_is_True():
    assert is_yesish('TrUe')

def test_is_yesish_yes_is_True():
    assert is_yesish('YeS')

def test_is_yesish_0_is_False():
    assert not is_yesish('0')

def test_is_yesish_false_is_False():
    assert not is_yesish('FaLsE')

def test_is_yesish_no_is_False():
    assert not is_yesish('No')

def test_is_yesish_junk_is_False():
    assert not is_yesish('Oh yeah junk')

def test_is_yesish_chokes_on_int():
    pytest.raises(AttributeError, is_yesish, 1)

def test_is_yesish_chokes_on_bool():
    pytest.raises(AttributeError, is_yesish, True)
