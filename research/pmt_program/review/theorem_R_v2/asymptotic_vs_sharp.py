"""Compare the ASYMPTOTIC_WITNESS value max_{theta<=asin eta} |sin((k-1) theta)| with the sharp value
G_k(eta) = max_{theta<=asin eta} |1 - w(theta)^{k-1}|, k = 2..10, eta on a grid in (0,1]."""
import json, math
import numpy as np
rows = []
for k in range(2, 11):
    n = k - 1
    for eta in np.linspace(0.01, 1.0, 100):
        t = np.linspace(0, math.asin(eta), 20001)
        asym = float(np.max(np.abs(np.sin(n * t))))
        sharp = float(np.max(np.abs(1 - (np.cos(t) * np.exp(1j * t)) ** n)))
        rows.append({"k": k, "eta": float(eta), "asymptotic": asym, "sharp": sharp, "gap": sharp - asym})
summ = {str(k): {"min_gap": min(r["gap"] for r in rows if r["k"] == k), "max_gap": max(r["gap"] for r in rows if r["k"] == k)} for k in range(2, 11)}
with open("outputs/asymptotic_vs_sharp.json", "w", newline="\n") as fh:
    json.dump({"summary_by_k": summ, "rows": rows}, fh, indent=1)
print(json.dumps(summ))
