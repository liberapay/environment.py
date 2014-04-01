from __future__ import absolute_import, division, print_function, unicode_literals

import pytest
from environment import Environment, is_yesish


def test_Environment_basically_works():
    env = Environment('FOO_', environ={'FOO_BAR': 'baz'})
    assert env.foo.bar == 'baz'

def test_Environment_unprefixed_works():
    env = Environment('FOO', environ={'FOO': 'baz'})
    assert env.foo == 'baz'


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
