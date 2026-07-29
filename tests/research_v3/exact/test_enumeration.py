from seion_core.research_v3.tree_enumeration import (
    count_fixed_arity,
    count_mixed,
    full_ordered_shapes,
    label_shape,
)
from seion_core.research_v3.typed_tree import tree_hash


def test_catalan_and_fuss_catalan_target_counts():
    assert [count_fixed_arity(k, 2) for k in range(1, 9)] == [1, 2, 5, 14, 42, 132, 429, 1430]
    assert [count_fixed_arity(k, 3) for k in range(1, 6)] == [1, 3, 12, 55, 273]
    assert [count_fixed_arity(k, 4) for k in range(1, 5)] == [1, 4, 22, 140]


def test_mixed_arity_grammar_exact_counts_through_five():
    assert [count_mixed(k) for k in range(1, 6)] == [3, 27, 333, 4752, 73764]


def test_every_binary_shape_through_eight_has_unique_ordered_hash():
    hashes = [
        tree_hash(label_shape(shape))
        for k in range(1, 9)
        for shape in full_ordered_shapes(k, 2)
    ]
    assert len(hashes) == 2055
    assert len(set(hashes)) == len(hashes)
