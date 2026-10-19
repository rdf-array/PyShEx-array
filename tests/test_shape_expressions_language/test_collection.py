""" RDF-: validating sequence terms against the Collection shape expression, ((shapeExpr))[min, max].

The data is Turtle- parsed by rdflib-array, where `(1 2 3)` is one sequence term, not an
rdf:first/rdf:rest ladder.
"""
import pytest
from rdflib import Graph, Namespace, URIRef
from rdflib.term import Sequence

from pyshex import ShExEvaluator

EX = Namespace("http://a.example/")
PREFIXES = "PREFIX : <http://a.example/>\nPREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\n"


def validate(schema: str, data: str, focus: str = EX.x) -> bool:
    results = ShExEvaluator(rdf=PREFIXES + data, schema=PREFIXES + schema, focus=focus, start=EX.S).evaluate()
    assert len(results) == 1
    return results[0].result


def reason(schema: str, data: str) -> str:
    return ShExEvaluator(rdf=PREFIXES + data, schema=PREFIXES + schema, focus=EX.x, start=EX.S).evaluate()[0].reason or ""


def test_a_sequence_of_the_right_length_whose_elements_conform():
    assert validate(":S { :p ((LITERAL))[3] }", ":x :p (1 2 3) .")


def test_the_bounds():
    assert not validate(":S { :p ((LITERAL))[2] }", ":x :p (1 2 3) .")
    assert validate(":S { :p ((LITERAL))[2, 3] }", ":x :p (1 2 3) .")
    assert not validate(":S { :p ((LITERAL))[4, *] }", ":x :p (1 2 3) .")
    assert validate(":S { :p ((LITERAL))[1,] }", ":x :p (1 2 3) .")
    assert validate(":S { :p ((LITERAL)) }", ":x :p (1 2 3) .")
    assert "3 elements where 2 expected" in reason(":S { :p ((LITERAL))[2] }", ":x :p (1 2 3) .")


def test_the_empty_sequence():
    assert validate(":S { :p ((IRI))[0] }", ":x :p () .")
    assert validate(":S { :p ((IRI)) }", ":x :p () .")
    assert not validate(":S { :p ((IRI))[1, *] }", ":x :p () .")


def test_elements_that_fail():
    assert not validate(":S { :p ((IRI)) }", ":x :p (:a 1 :b) .")
    assert validate(":S { :p ((IRI OR LITERAL)) }", ":x :p (:a 1 :b) .")


def test_wants_a_sequence():
    assert not validate(":S { :p ((LITERAL)) }", ":x :p 1 .")
    assert "expected: sequence" in reason(":S { :p ((LITERAL)) }", ":x :p 1 .")


def test_a_sequence_is_none_of_the_node_kinds_but_matches_dot():
    assert validate(":S { :p . }", ":x :p (1 2) .")
    assert not validate(":S { :p LITERAL }", ":x :p (1 2) .")
    assert not validate(":S { :p IRI }", ":x :p (1 2) .")
    assert not validate(":S { :p NONLITERAL }", ":x :p (1 2) .")
    assert validate(":S { :p NOT LITERAL }", ":x :p (1 2) .")


def test_nesting():
    assert validate(":S { :p ((((LITERAL))[2]))[2] }", ":x :p ((1 2) (3 4)) .")
    assert not validate(":S { :p ((((LITERAL))[2]))[2] }", ":x :p ((1 2) (3)) .")
    assert not validate(":S { :p ((((LITERAL))[2]))[2] }", ":x :p ((1 2) 3) .")


def test_shape_references_from_the_elements():
    data = ":x :p (:a :b) . :a :q 1 . :b :q 2 ."
    assert validate(":S { :p ((@:T))[2] }\n:T { :q LITERAL }", data)
    assert not validate(":S { :p ((@:T))[2] }\n:T { :q IRI }", data)


def test_a_sequence_as_the_focus_node():
    g = Graph()
    g.parse(data=PREFIXES + "(1 2) :q :o .", format="turtle")
    seq = next(g.subjects(EX.q, EX.o))
    assert isinstance(seq, Sequence)
    for schema, expected in [(":S ((LITERAL))[2]", True), (":S ((LITERAL))[3]", False), (":S { :q [:o] }", True)]:
        results = ShExEvaluator(rdf=g, schema=PREFIXES + schema, focus=seq, start=EX.S).evaluate()
        assert len(results) == 1 and results[0].focus == seq
        assert results[0].result is expected, f"{schema}: {results[0].reason}"


def test_a_sequence_in_a_shape_map_is_a_json_array():
    from pyshex.shapemap_structure_and_language.p3_shapemap_structure import ShapeAssociation

    assoc = ShapeAssociation([{"value": "1", "type": "http://www.w3.org/2001/XMLSchema#integer"}, "http://a.example/x"],
                             EX.S) if False else None
    # the node selector is the array of the elements' n3 forms, as the shex.js and Jena RDF- forks read them
    assoc = ShapeAssociation(["http://a.example/x", "_:b1"], EX.S)
    assert isinstance(assoc.nodeSelector, Sequence)
    assert assoc.nodeSelector[0] == URIRef("http://a.example/x")
