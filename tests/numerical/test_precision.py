from seion_core.numerics.precision import precision_info


def test_precision_tiers_record_machine_epsilon():
    for precision in ["float32", "float64", "complex64", "complex128"]:
        info = precision_info(precision)
        assert info["machine_epsilon"] > 0

