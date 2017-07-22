from .import_context import boothby
from boothby import revision_constraint
import re


def test_is_fixed():
    assert revision_constraint.is_fixed( "1" ) == True
    assert revision_constraint.is_fixed( "1.2" ) == True
    assert revision_constraint.is_fixed( "1.2.3" ) == True
    assert revision_constraint.is_fixed( "1.5.9" ) == True
    assert revision_constraint.is_fixed( "1.2.3_119" ) == True
    assert revision_constraint.is_fixed( "1_2234" ) == True

    assert revision_constraint.is_fixed( "[1.3,2.5.9]" ) == False
    assert revision_constraint.is_fixed( "[1.5,2.5.9)" ) == False
    assert revision_constraint.is_fixed( "(1.3,2.5.9]" ) == False
    assert revision_constraint.is_fixed( "(1.5,2.5.9)" ) == False

    assert revision_constraint.is_fixed("1.2.+") == False
    assert revision_constraint.is_fixed("1+") == False
    assert revision_constraint.is_fixed("+") == False

    assert revision_constraint.is_fixed( "1-randomGarbage_package9" ) == True

    # you could interpret [1.1,1.1] as fixed, however you ended
    # up with those numbers in the file, you were attempting
    # to create a dynamic revision range
    assert revision_constraint.is_fixed( "[1.5,1.5]" ) == False

def test_regex_functionality():
    make_regex = revision_constraint.make_constraint_regex
    funky_re = make_regex("1.99.+")
    assert bool(re.match(funky_re, "1")) == False
    assert bool(re.match(funky_re, "1.99.0")) == True
    assert bool(re.match(funky_re, "1.99.298")) == True
    # ambiguous, more a regression test than a unittest
    assert bool(re.match(funky_re, "1.99.")) == True

def test_make_constraint():
    make_functor = revision_constraint.make_constraint_functor
    assert ( make_functor("1.3.+") )("1.3.5") == True
    assert ( make_functor("1.3.+") )("1.3.5.1") == True
    assert ( make_functor("1.3.+") )("1.3.555.444_999") == True
    assert ( make_functor("1.3.+") )("1.2.3.5.1") == False
    assert ( make_functor("1.3.+") )("999.1.3.5") == False
