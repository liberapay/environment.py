from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import pytest
from environment import Environment, is_yesish


if sys.version_info < (3, 0, 0):
    str_type = unicode
else:
    str_type = str


def test_Environment_basically_works():
    env = Environment(FOO_BAR=str_type, _environ={'FOO_BAR': 'baz'})
    assert env.foo_bar == 'baz'
    assert env.missing == []
    assert env.malformed == []

def test_Environment_unprefixed_works():
    env = Environment(FOO=str_type, _environ={'FOO': 'baz'})
    assert env.foo == 'baz'

def test_Environment_missing_is_missing():
    env = Environment(FOO=str_type, _environ={})
    assert env.missing == ['FOO']

def test_Environment_malformed_is_malformed():
    env = Environment(FOO=int, _environ={'FOO': 'baz'})
    assert env.malformed == [('FOO', "ValueError: invalid literal for int() with base 10: 'baz'")]

def test_Environment_extra_is_ignored():
    env = Environment(FOO=str_type, _environ={'FOO_BAR_BAZ': '42'})
    assert env.missing == ['FOO']
    assert sorted(env.__dict__.keys()) == ['environ', 'malformed', 'missing', 'prefix']

def test_Environment_typecasting_works():
    env = Environment(FOO=int, _environ={'FOO': '42'})
    assert env.foo == 42

def test_Environment_complex_typecasting_works():
    class MyType(object):
        def __init__(self, val):
            self.val = 'cheese'
    env = Environment(FOO=MyType, _environ={'FOO': '42'})
    assert env.foo.val == 'cheese'

def test_Environment_prefixing_works():
    env = Environment('FOO_', BAR=str_type, _environ={'FOO_BAR': '42'})
    assert env.bar == '42'

def test_Environment_prefixing_works_arbitrarily():
    env = Environment('FOO_BA', R_BAZ=int, _environ={'FOO_BAR_BAZ': '42'})
    assert env.r_baz == 42

def test_Environment_malformed_values_dont_generate_namespaces():
    env = Environment(FOO_BAR_BAZ=int, _environ={'FOO_BAR_BAZ': 'blah'})
    assert 'foo' not in env.__dict__


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
