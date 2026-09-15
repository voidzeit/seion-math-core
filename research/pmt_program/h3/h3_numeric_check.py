import math, random
def val(th):
    C=1.0; S=0.0
    for t in th: C*=math.cos(t); S+=t
    return math.sqrt(max(0.0,1-2*C*math.cos(S)+C*C))
def capped(al, N=20000):
    best=0.0
    for g in range(N+1):
        t=(math.pi/2)*g/N
        v=val([min(a,t) for a in al]); best=max(best,v)
    return best
def ascend(al, th):
    best=val(th)
    for sweep in range(60):
        before=best
        for i,a in enumerate(al):
            bt=th[i]; bv=best
            for g in range(81):
                th[i]=a*g/80; v=val(th)
                if v>bv: bv,bt=v,th[i]
            lo=max(0,bt-a/80); hi=min(a,bt+a/80)
            for _ in range(50):
                m1=lo+(hi-lo)/3; m2=hi-(hi-lo)/3
                th[i]=m1; v1=val(th); th[i]=m2; v2=val(th)
                if v1<v2: lo=m1
                else: hi=m2
            th[i]=(lo+hi)/2
            if val(th)>=bv: bv,bt=val(th),th[i]
            th[i]=bt; best=bv
        if best-before<1e-14: break
    return best
random.seed(7)
worst=0.0; trials=0
for trial in range(400):
    n=random.randint(2,7)
    mode=random.random()
    if mode<0.3: etas=[random.random() for _ in range(n)]
    elif mode<0.6: etas=[random.random()**3 for _ in range(n)]
    else: etas=[random.choice([0.05,0.3,0.7,0.95,1.0,random.random()]) for _ in range(n)]
    al=[math.asin(min(e,1)) for e in etas]
    cap=capped(al)
    starts=[al[:], [0.0]*n] + [[a*random.random() for a in al] for _ in range(25)]
    # vertex-type starts
    starts += [[a if random.random()<0.5 else 0.0 for a in al] for _ in range(10)]
    b=max(ascend(al,s[:]) for s in starts)
    worst=max(worst,b-cap); trials+=1
    if b-cap>1e-7: print("COUNTEREXAMPLE?", etas, b, cap)
print("trials",trials,"max(multistart - capped) =",worst)
