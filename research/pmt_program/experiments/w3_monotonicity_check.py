"""Exact check of the monotonicity step in the W_3 proof (Paper I, Prop. 5.4).
f(u,v) = ((u+v)^2 + u^2 v^2) / ((1+u^2)(1+v^2)).  Claim: d f/du >= 0 on [0,sqrt2]^2 (and by symmetry d/dv)."""
import sympy as sp
u, v = sp.symbols('u v', nonnegative=True)
f = ((u+v)**2 + u**2*v**2) / ((1+u**2)*(1+v**2))
num = sp.factor(sp.numer(sp.together(sp.diff(f, u))))
den = sp.factor(sp.denom(sp.together(sp.diff(f, u))))
print("df/du numerator :", num)
print("df/du denominator:", den)
# numerator is 2*(1+v^2)*h(u,v); inspect h
h = sp.factor(num / (2*(1+v**2))) if sp.simplify(num % 1) == 0 else num
print("h =", sp.expand(h))
# SOS identity for the global bound
print("4(1+u^2)(1+v^2) - 3((u+v)^2+u^2v^2) - [(uv-2)^2+(u-v)^2] =",
      sp.expand(4*(1+u**2)*(1+v**2) - 3*((u+v)**2 + u**2*v**2) - ((u*v-2)**2 + (u-v)**2)))
# closed form for f as function of angles: q=sin a, s=sin b
a, b = sp.symbols('a b', real=True)
g = sp.sin(a)**2 + sp.cos(a)**2*sp.sin(b)**2 + 2*sp.sin(a)*sp.cos(a)*sp.sin(b)*sp.cos(b)
print("f - [sin^2(a+b) + sin^2 a sin^2 b] =", sp.simplify(g - (sp.sin(a+b)**2 + sp.sin(a)**2*sp.sin(b)**2)))
