"""Relationship between the orders: sample O2-dominated states and test O1 against the same chain datum, and vice versa."""
import json, math
import numpy as np
from states import sample_thetas, chain_state, sample_child_O2, sample_child_O1, gram_state, o1_violation, o2_violation
rng = np.random.default_rng(5)
res = {"O2_states_failing_O1": 0, "O1_states_failing_O2": 0, "n": 0, "max_O1_violation_of_O2_states": -1.0, "max_O2_violation_of_O1_states": -1.0}
for i in range(40000):
    eta = float(rng.choice([0.1, 0.3, 0.6, 0.9]))
    rho, chi = chain_state(sample_thetas(rng, eta, int(rng.integers(1, 4))))
    F, R = sample_child_O2(rng, rho, chi); a, r, c, psi = gram_state(F, R)
    v1 = o1_violation(a, r, psi, rho, chi)[0]
    res["max_O1_violation_of_O2_states"] = max(res["max_O1_violation_of_O2_states"], v1)
    res["O2_states_failing_O1"] += v1 > 1e-9
    F, R = sample_child_O1(rng, rho, chi); a, r, c, psi = gram_state(F, R)
    v2 = o2_violation(a, r, c, rho, chi)
    res["max_O2_violation_of_O1_states"] = max(res["max_O2_violation_of_O1_states"], v2)
    res["O1_states_failing_O2"] += v2 > 1e-9
    res["n"] += 1
res = {k: (int(v) if isinstance(v, (np.integer, bool, np.bool_)) else v) for k, v in res.items()}
json.dump(res, open("outputs/order_relation.json", "w"), indent=1); print(json.dumps(res))
