#!/usr/bin/env python3
from __future__ import annotations
import argparse,itertools,math
from collections import Counter
from fractions import Fraction
M=2520; DS=[2,3,6,7,8,9,10,15]; FULL=[7,8,9,15]; ORIENTED=[6,10]; PS=[2,3,5,7]
ROWS=[
(7,'d',2213459,1414,65,479),(7,'d',15312283,9262,113,7),(9,'d',13,7,2,13),
(6,'2',1,2,3,3),(7,'2',1,2,3,3),(7,'2',2,17,71,71),(7,'2',17,76271,21063928,79),
(8,'2',1,2,3,3),(8,'2',43,96222,30042907,109),(9,'2',1,2,3,3),
(10,'2',1,2,3,3),(15,'2',1,2,3,3),(8,'3',1549034,33,15613,2)]
I={d:i for i,d in enumerate(DS)}
def mask(n):
 m=0
 for i,d in enumerate(DS):
  if n%d==0:m|=1<<i
 return m
def has(m,d):return bool(m&(1<<I[d]))
def event(a,b,c):
 for d in FULL:
  for x,y,z in set(itertools.permutations((2,3,d))):
   if has(a,x) and has(b,y) and has(c,z):return True
 for d in ORIENTED:
  if has(c,d) and ((has(a,2) and has(b,3)) or (has(a,3) and has(b,2))):return True
  if has(c,2) and ((has(a,d) and has(b,3)) or (has(a,3) and has(b,d))):return True
 return False
def dens(k=1):
 C=Counter(mask(k*n%M) for n in range(M));t=0
 for a,ca in C.items():
  for b,cb in C.items():
   for c,cc in C.items():
    if event(a,b,c):t+=ca*cb*cc
 return Fraction(t,M**3)
def val(n,p):
 v=0
 while n%p==0:v+=1;n//=p
 return v
def verify():
 for d,o,a,b,c,p in ROWS:
  ok=a*a+b**3==c**d if o=='d' else a**d+b**3==c*c if o=='2' else a*a+b**d==c**3
  assert ok and val(c if o=='2' else a,p)==1
 t=dens();assert t==Fraction(2338961,9261000)
 s1=s2=Fraction()
 for n in range(5):
  for S in itertools.combinations(PS,n):
   k=math.prod(S);mu=(-1)**n
   s1+=Fraction(mu,k**3)*dens(k);s2+=Fraction(mu,k**3)*dens(2*k)
 assert s1==Fraction(119417,771750) and s2==Fraction(8188,18375)
 e=math.prod(Fraction(p**3-1,p**3) for p in PS)
 c=(s1+s2/8)/e;assert c==Fraction(40601,160797)
 q=Fraction(9,8)-c;assert q==Fraction(1122365,1286376)
 N=10000;z=sum(1/n**3 for n in range(1,N+1));lo=z+1/(2*(N+1)**2);hi=z+1/(2*N*N)
 D=sorted([1-float(q)/lo,1-float(q)/hi])
 assert D[0]<0.27415956281325<D[1]
 return t,s1,s2,q,D
def main():
 argparse.ArgumentParser().parse_args();t,s1,s2,q,D=verify()
 print('global Beal density replay valid')
 print('periodic density:',t)
 print('mobius sums:',s1,s2)
 print('density: 1-%s/zeta(3)'%q)
 print('certified interval:',D)
if __name__=='__main__':main()
