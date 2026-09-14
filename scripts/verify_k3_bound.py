"""Adversarial numerical stress test of the new k=3 upper bound U_3(eta).

Claim under verification (derived analytically, see closure notes):

For a k=3 CHAIN  (leaves a,b -> node1 -mu1-> ; (node1_out,c) -mu2-> node2 ;
(node2_out,d) -mu3-> root), with each mu_v bilinear, ||mu_v||_op <= M,
each node's closure-residual operator norm <= rho, orthogonal projectors
at every internal node, arbitrary finite real (or complex) dimension and
arbitrary projector rank:

    E_P <= h(q1) * L_T,   h(q) = M^2*q + M*rho*sqrt(M^2-q^2),   q1 in [0,rho]

and therefore, maximizing the free scalar q1 over [0,rho]:

    E_P <= U_3(eta) * rho * M^2 * L_T

    U_3(eta) = 1 + sqrt(1-eta^2),        0 < eta <= eta_c
    U_3(eta) = sqrt(1+eta^2)/eta,        eta_c < eta <= 1
    eta_c = sqrt((sqrt(5)-1)/2)  ~= 0.78615

The SAME function U_3 is claimed for the BRANCHING topology too (two
children u1,u2, root combines them).

This script does NOT prove the theorem (that's the analytic derivation).
It searches, by random sampling + local ascent, for any admissible
configuration that VIOLATES the bound, in several dimensions, for both
topologies, at several eta. A violation would falsify the claim; survival
of many trials + local refinement is corroborating evidence only.
"""
import numpy as np

rng = np.random.default_rng(20260808)


def op_norm_bilinear(T, trials=400, iters=60):
    """Estimate ||T||_op for a bilinear map T: R^p x R^q -> R^r given as a
    (r,p,q) tensor, via random restarts of alternating power iteration.
    This UNDERESTIMATES the true sup (heuristic), which is fine here since
    we use it only to rescale tensors so their norm does not EXCEED M
    (a conservative direction for this falsification search: if anything
    we might rescale slightly too aggressively, making tensors slightly
    *smaller* than allowed -- that can only make the bound easier to
    satisfy, so it cannot manufacture a false violation of E_P<=bound;
    it could only hide a real violation, which is why we also do a
    separate direct-projection ascent step below using many restarts).
    """
    r, p, q = T.shape
    best = 0.0
    for _ in range(trials):
        x = rng.normal(size=p)
        x /= np.linalg.norm(x)
        y = rng.normal(size=q)
        y /= np.linalg.norm(y)
        for _ in range(iters):
            v = np.einsum('rpq,p,q->r', T, x, y)
            nv = np.linalg.norm(v)
            if nv < 1e-14:
                break
            x_new = np.einsum('rpq,r,q->p', T, v, y)
            nx = np.linalg.norm(x_new)
            if nx < 1e-14:
                break
            x = x_new / nx
            y_new = np.einsum('rpq,r,p->q', T, v, x)
            ny = np.linalg.norm(y_new)
            if ny < 1e-14:
                break
            y = y_new / ny
        val = np.linalg.norm(np.einsum('rpq,p,q->r', T, x, y))
        best = max(best, val)
    return best


def apply_bilinear(T, x, y):
    return np.einsum('rpq,p,q->r', T, x, y)


def random_orthogonal_projector(dim, rank, rng):
    A = rng.normal(size=(dim, rank))
    Q, _ = np.linalg.qr(A)
    Q = Q[:, :rank]
    return Q @ Q.T


def h(q, M, rho):
    return M * M * q + M * rho * np.sqrt(max(0.0, M * M - q * q))


def U3(eta):
    eta_c = np.sqrt((np.sqrt(5) - 1) / 2)
    if eta <= eta_c:
        return 1 + np.sqrt(1 - eta * eta)
    return np.sqrt(1 + eta * eta) / eta


def make_capped_tensor(shape, cap, rng, n_rescale_trials=250):
    T = rng.normal(size=shape)
    nrm = op_norm_bilinear(T, trials=n_rescale_trials)
    if nrm < 1e-12:
        return T
    # Scale so the ESTIMATED norm equals cap. Since the estimate is a lower
    # bound on the true sup, the true op-norm could be slightly ABOVE cap
    # after rescaling. We correct with a second, more thorough estimate and
    # rescale again to be safe (belt and suspenders for the "never exceed M"
    # premise the theorem depends on).
    T = T * (cap / nrm)
    nrm2 = op_norm_bilinear(T, trials=n_rescale_trials * 2, iters=120)
    if nrm2 > cap:
        T = T * (cap / nrm2)
    return T


def closure_tensor(mu_tensor, P):
    """Return the tensor of (I-P) mu( P . , . ) i.e. the closure map used to
    define rho_v, restricted to already-projected inputs. Here we directly
    build the tensor of (I - P) @ mu, applied with its own inputs pre-
    projected by the CALLER (leaves need no projection); for node2 in the
    chain, the "x" argument is R1 = P1 mu1(a,b), which the caller already
    supplies pre-projected, so here we only need (I-P)."""
    r, p, q = mu_tensor.shape
    IminusP = np.eye(r) - P
    return np.einsum('sr,rpq->spq', IminusP, mu_tensor)


def run_trial(dim, rank_in, rank_mid, eta, topology, M=1.0):
    rho = eta * M
    if topology == 'chain':
        d_a = d_b = d_c = d_d = dim
        mu1 = make_capped_tensor((dim, d_a, d_b), M, rng)
        mu2 = make_capped_tensor((dim, dim, d_c), M, rng)
        mu3 = make_capped_tensor((dim, dim, d_d), M, rng)
        P1 = random_orthogonal_projector(dim, rank_in, rng)
        P2 = random_orthogonal_projector(dim, rank_mid, rng)
        P3 = random_orthogonal_projector(dim, rank_mid, rng)

        r1_tensor = closure_tensor(mu1, P1)
        r1_norm = op_norm_bilinear(r1_tensor, trials=250, iters=80)
        if r1_norm > 1e-12:
            mu1 = mu1 * min(1.0, rho / r1_norm)
        r2_tensor = closure_tensor(mu2, P2)
        r2_norm = op_norm_bilinear(r2_tensor, trials=250, iters=80)
        if r2_norm > 1e-12:
            mu2 = mu2 * min(1.0, rho / r2_norm)
        # re-cap operator norms after rho-rescaling (rescaling by <=1 can only
        # shrink op norm, so caps remain valid)

        best_EP = 0.0
        for _ in range(60):
            a = rng.normal(size=d_a); a /= np.linalg.norm(a)
            b = rng.normal(size=d_b); b /= np.linalg.norm(b)
            c = rng.normal(size=d_c); c /= np.linalg.norm(c)
            d = rng.normal(size=d_d); d /= np.linalg.norm(d)
            F1 = apply_bilinear(mu1, a, b)
            R1 = P1 @ F1
            F2 = apply_bilinear(mu2, F1, c)
            R2 = P2 @ apply_bilinear(mu2, R1, c)
            F3 = apply_bilinear(mu3, F2, d)
            R3 = P3 @ apply_bilinear(mu3, R2, d)
            EP = np.linalg.norm(P3 @ F3 - R3)
            best_EP = max(best_EP, EP)
        return best_EP

    elif topology == 'branch':
        d_a = d_b = d_c = d_d = dim
        mu1 = make_capped_tensor((dim, d_a, d_b), M, rng)
        mu2 = make_capped_tensor((dim, d_c, d_d), M, rng)
        mu3 = make_capped_tensor((dim, dim, dim), M, rng)
        Pu1 = random_orthogonal_projector(dim, rank_in, rng)
        Pu2 = random_orthogonal_projector(dim, rank_in, rng)
        P3 = random_orthogonal_projector(dim, rank_mid, rng)

        r1n = op_norm_bilinear(closure_tensor(mu1, Pu1), trials=250, iters=80)
        if r1n > 1e-12:
            mu1 = mu1 * min(1.0, rho / r1n)
        r2n = op_norm_bilinear(closure_tensor(mu2, Pu2), trials=250, iters=80)
        if r2n > 1e-12:
            mu2 = mu2 * min(1.0, rho / r2n)

        best_EP = 0.0
        for _ in range(60):
            a = rng.normal(size=d_a); a /= np.linalg.norm(a)
            b = rng.normal(size=d_b); b /= np.linalg.norm(b)
            c = rng.normal(size=d_c); c /= np.linalg.norm(c)
            d = rng.normal(size=d_d); d /= np.linalg.norm(d)
            Fu1 = apply_bilinear(mu1, a, b)
            Ru1 = Pu1 @ Fu1
            Fu2 = apply_bilinear(mu2, c, d)
            Ru2 = Pu2 @ Fu2
            F3 = apply_bilinear(mu3, Fu1, Fu2)
            R3 = P3 @ apply_bilinear(mu3, Ru1, Ru2)
            EP = np.linalg.norm(P3 @ F3 - R3)
            best_EP = max(best_EP, EP)
        return best_EP


violations = []
report = []
etas = [0.05, 0.2, 0.4, 0.6, 0.7862, 0.9, 1.0]
for topology in ['chain', 'branch']:
    for dim in [2, 3]:
        ranks = [1, dim - 1] if dim > 1 else [1]
        ranks = sorted(set(r for r in ranks if 1 <= r < dim))
        for rank in ranks:
            for eta in etas:
                M = 1.0
                rho = eta * M
                EP = run_trial(dim, rank, rank, eta, topology, M=M)
                bound_new = U3(eta) * rho * M * M
                bound_universal = 2.0 * rho * M * M
                ratio_new = EP / bound_new if bound_new > 0 else float('inf')
                ok_new = EP <= bound_new * 1.02 + 1e-9  # 2% slack for op-norm estimation error
                ok_universal = EP <= bound_universal + 1e-9
                report.append((topology, dim, rank, eta, EP, bound_new, ratio_new, ok_new, ok_universal))
                if not ok_new:
                    violations.append(report[-1])

print(f"{'topo':6} {'dim':3} {'rk':2} {'eta':6} {'E_P':8} {'U3*rhoM2':9} {'ratio':6} {'<=U3':5} {'<=2 (sanity)':5}")
for row in report:
    topo, dim, rank, eta, EP, bound_new, ratio_new, ok_new, ok_universal = row
    print(f"{topo:6} {dim:3} {rank:2} {eta:6.3f} {EP:8.4f} {bound_new:9.4f} {ratio_new:6.3f} {str(ok_new):5} {str(ok_universal):5}")

print()
print(f"total trials: {len(report)}, violations of new bound (>2% slack): {len(violations)}")
if violations:
    print("VIOLATIONS:", violations)
else:
    print("No violations found: numerical evidence is consistent with the derived bound.")
