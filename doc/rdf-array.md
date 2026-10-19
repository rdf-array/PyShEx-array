# PyShEx-array: ShEx over RDF- (sequences as terms)

RDF- is RDF whose data model has a fifth kind of term, the **sequence**: `(1 2 3)` in Turtle-
is one term holding its elements in order, not a ladder of `rdf:first`/`rdf:rest` blank nodes,
and `()` is the empty sequence, not `rdf:nil`. Triples that spell out `rdf:first`/`rdf:rest`
are still ordinary triples and `rdf:nil` an ordinary IRI; they are just no longer what `( … )`
means. ShEx- adds one shape expression for sequences, the **Collection**. This repository is the
Python validator; the Python stack is

| role | fork (branch `rdf-sequences`) | of |
|---|---|---|
| RDF data model, parsers, serializers, SPARQL | [rdflib-array](https://github.com/rdf-array/rdflib-array), `rdflib.term.Sequence` | [RDFLib/rdflib](https://github.com/RDFLib/rdflib) 7.7.0a0 |
| ShExC parser and writer, `pyshexc` | [grammar-python-antlr-linkml-array](https://github.com/rdf-array/grammar-python-antlr-linkml-array) | [ericprud/grammar-python-antlr-linkml](https://github.com/ericprud/grammar-python-antlr-linkml), branch `extends-shaperef` |
| ShExJ objects and ShExC writer, `ShExJSG` | [ShExJSG-array](https://github.com/rdf-array/ShExJSG-array) | [linkml/ShExJSG](https://github.com/linkml/ShExJSG) |
| collection flattener behind `shexeval -cf`, `CFGraph` | [CFGraph-array](https://github.com/rdf-array/CFGraph-array) | [linkml/CFGraph](https://github.com/linkml/CFGraph) |
| validator, `pyshex` | this repository | [linkml/PyShEx](https://github.com/linkml/PyShEx) |

`pyjsg`, `sparqlslurper`, `rdflib-shim` and `SPARQLWrapper` are used unchanged. The same
treatment of other implementations: [jena-array](https://github.com/rdf-array/jena-array) (Java)
and [shex.js-array](https://github.com/rdf-array/shex.js-array) (JavaScript), each with its own
dependency forks.

## The Collection shape expression

```shex
((shapeExpr))            # a sequence, of any length, of nodes conforming to shapeExpr
((shapeExpr))[m]         # exactly m elements
((shapeExpr))[m, n]      # from m to n elements
((shapeExpr))[m, *]      # at least m elements  (also written [m,])
```

A Collection is a shape atom: it takes `NOT`, `AND` and `OR`, nests (`((((LITERAL))[2]))` is a
sequence of pairs), is a triple constraint's value or an `EXTENDS` target, and may be the top of a
shape declaration. `((x))` is always a Collection and `(x)` a parenthesised shape expression: in
`grammar/ShExDoc.g4` (in the parser fork) the `shapeAtomCollection` and
`inlineShapeAtomCollection` alternatives come before the parenthesised ones, and
`collectionBounds` is `'[' INTEGER (',' (INTEGER | '*')?)? ']'`.

Semantics (`satisfiesCollection` in `pyshex/shape_expressions_language/p5_3_shape_expressions.py`):
the focus node conforms iff it is a `Sequence`, its length is within the bounds, and every element
satisfies `shapeExpr`, each element being a focus node of its own (so `@<S>` on an element is
checked against the element's triples). A sequence satisfies no node kind (`IRI`, `BNODE`,
`LITERAL`, `NONLITERAL`), no datatype and no value set, but matches `.`. The failure reasons read
`Node kind mismatch have: URIRef expected: sequence`, `Sequence of 2 elements where 3 expected`
(or `at least 1`, `1 to 3`), or the failing element's own reason.

In ShExJ (`ShExJSG/ShExJ.jsg`, `ShExJSG/ShExJ.py`):

```json
{ "type": "Collection", "shapeExpr": { "type": "NodeConstraint", "nodeKind": "literal" }, "min": 3, "max": 3 }
```

`min` and `max` are optional (absent: unbounded; `max` is `-1` for `*`). `Collection` is in the
`shapeExpr` union everywhere a shape expression may appear; both ShExC writers (`ShExJSG.ShExC`
and `pyshexc.ShExC`) write it as `(( … ))[m, n]`.

## Sequences as nodes

`rdflib.term.Sequence` is a node like any other in PyShEx: a shape map's node (`Node` in
`pyshex/shapemap_structure_and_language/p1_notation_and_terminology.py`), a focus node, a triple
constraint's value and a result's `focus`. Pass one through the API:

```python
from rdflib import Graph, Literal, URIRef
from rdflib.term import Sequence
from pyshex import ShExEvaluator

g = Graph().parse(data='<http://a.example/s> <http://a.example/p> (1 2 3) .', format="turtle")
schema = """PREFIX : <http://a.example/>
:S { :p ((LITERAL))[3] }
:T ((LITERAL))[1, *]"""
ShExEvaluator(g, schema, focus=URIRef("http://a.example/s"), start="http://a.example/S").evaluate()
ShExEvaluator(g, schema, focus=Sequence([Literal(1), Literal("x")]), start="http://a.example/T").evaluate()
```

`shexeval`'s `-fn` focus argument and the ShapeMap language have no syntax for a sequence node;
the API is the way to validate one. A sequence in a result (`EvaluationResult.focus`) is the
rdflib `Sequence`; `pyshex/utils/n3_mapper.py` renders it as `( … )` in messages.

`shexeval -cf` wraps the data in a `CFGraph` (CFGraph-array), which flattens each sequence
object into one triple per element, nested sequences included, so a schema written
`{ :p LITERAL+ }` validates `<s> :p (1 2 3)`; it still flattens explicit ladders too.

## What changed, per repository

- **PyShEx-array** (this repository): `satisfiesCollection` and its dispatch in
  `p5_3_shape_expressions.py`; the reference walks in `p5_context.py`, `utils/schema_utils.py`,
  `shexmap/bindings.py` and the `EXTENDS` index descend into a Collection's `shapeExpr`;
  `shexmap/materializer.py` accepts a Collection as a node constraint whose value must be a
  sequence; `Node` and `ShapeAssociation` admit sequences; `shex_evaluator.normalize_uri` leaves
  rdflib nodes alone; `pyproject.toml` pins the four forks in `[tool.uv.sources]`.
- **grammar-python-antlr-linkml-array**: `grammar/ShExDoc.g4`, the regenerated
  `pyshexc/parser/` (ANTLR 4.9.3, `scripts/genpython.sh`), `visitShapeAtomCollection` and
  `visitInlineShapeAtomCollection` in `parser_impl/shex_shape_expression_parser.py`, and the
  writer in `pyshexc/ShExC.py` (which also stopped wrapping `NOT`'s operand in a second pair of
  parentheses, since `NOT ((x))` would read as a Collection).
- **ShExJSG-array**: `Collection` in `ShExJ.jsg` and `ShExJ.py` (edited by hand to match the
  `.jsg`: `pyjsg`'s generator needs ANTLR runtime 4.13 while `pyshexc` pins 4.9.3; the ten inline
  `typing.Union[...]` shape-expression lists were widened too), and the writer in `ShExC.py`.
- **CFGraph-array**: `_flatten` yields one triple per (nested) element of a sequence object.
- **rdflib-array**: see its `docs/rdf-array.md`.

## Tests

New: `tests/test_shape_expressions_language/test_collection.py` (10 tests: lengths and bounds,
the empty sequence, failing elements, a non-sequence focus, node kinds versus `.`, nesting, shape
references from elements, a sequence as focus node and in a shape map) here;
`tests/test_collection.py` (6) in the parser fork; `tests/test_sequence.py` (3) in CFGraph-array.

Flagged, each with its reason in the test file, because the fixture describes a list as an
`rdf:first`/`rdf:rest` ladder, which under RDF- no sequence term matches:

- the shexTest validation entries `1list0PlusDot-empty_pass`, `1list0PlusDot-list_Iv1,Iv2,Iv3_pass`,
  `1list0PlusDot-list_Iv1,Iv2,Lx_pass`, `1list0PlusIri-empty_pass`,
  `1list0PlusIri-list_Iv1,Iv2,Iv3_pass` and `1list1PlusIri-list_Iv1,Iv2,Iv3_pass`
  (`expected_failures` in `tests/utils/manifest_tester.py`, counted in the run summary); their
  ShEx- forms are `((.))`, `((IRI))` and `((IRI))[1, *]`, and the `manualList` data, written as
  explicit `rdf:first` triples, still passes;
- `tests/test_biolink/test_biolink_items.py::test_new_meta` and
  `tests/test_notebooks/test_book_small_text.py::test_bibframe_work_conforms`
  (`xfail(strict=True)`): the biolink and bibframe schemas use ladder shapes;
- `tests/test_cli/output/evaluate/biolinkfail`, regenerated: the reported failure is now
  `Datatype constraint (xsd:string) does not match Sequence ("rdf" "rdfs" "xsd" "skos" "OIO")`,
  one sequence term where it used to be a blank node.

Pre-existing failures, which fail the same way on an unmodified checkout with the same
dependencies: in `tests/test_policy/test_dependencies.py`, two tests that map imports to
installed distributions and do not recognise the editable installs of the forks (`ShExJSG` is
reported as provided by no distribution); and the three shexTest manifest tests
(`test_manifest_shex_json`, `test_manifest_shex_shexc`, `test_generate_earl_report`) over the
entries `1dotShapeCode1fail_abort`, `extends-abstract-or_fail-via-X`,
`extends-abstract-or_fail-X-and-A`, `openOneInclude1dotclosecardPlusc1IRI_fail-b1d1aI1` (ShExJ
only) and the loading errors on `2val1refvsAnnot_pass` and `2val1refvsCode_pass` (annotations and
semantic actions on a shape declaration whose expression is a reference, which PyShEx's flattened
schema cannot carry). In the parser fork `tests/test_shexc.py::TestShExCValidation::test_shex_schema`
fails as before (the writer drops `{1}` in `1card1`, and a top-level `<S> (<T>)` yields no schema);
in ShExJSG-array `tests/test_shexc.py` fails on `1card1.json` and the eight `*Extends*.json`
schemas as before. The manifest tests fetch shexTest from GitHub.

## Setting up

`uv sync` in this repository installs the forks from GitHub (`[tool.uv.sources]`, with
`prerelease = "allow"` for rdflib-array's 7.7.0a0). To work on the stack itself, install the
sibling checkouts editable into one environment:

```bash
uv pip install --prerelease=allow -e ../rdflib-array -e ../ShExJSG-array -e ../CFGraph-array -e ../grammar-python-antlr-linkml-array
uv pip install --no-deps -e .
```

## Not done

- No ShapeMap syntax for a sequence node (`shexeval -fn`, `-fm`); use the API.
- The materializer (`shexmap`) checks that a Collection's value is a sequence but builds no
  sequences from element bindings.
- ShExR (schemas as RDF) is untouched: PyShEx reads ShExC and ShExJ only.
- `sparqlslurper` (`-ss`) is untouched; SPARQL endpoints return no sequence terms.
- shexTest has no RDF- tests; the Collection tests are the local ones listed above.
