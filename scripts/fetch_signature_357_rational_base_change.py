#!/usr/bin/env python3
"""Enumerate rational elliptic newforms that could base change to the open K7 levels.

At 3 the extension K7/Q is unramified, so a base-change packet with K7 conductor
exponent at most 3 comes from a rational curve with 3-adic conductor exponent at
most 3.  At 7 an elliptic curve over Q has conductor exponent at most 2.  Thus the
finite source list has conductor supported at 3 and 7 with exponents <=(3,2).
"""
from __future__ import annotations
import hashlib, json, os, sys
from decimal import Decimal
from typing import Any
import psycopg
DSN=os.environ.get('LMFDB_DSN','host=devmirror.lmfdb.xyz port=5432 dbname=lmfdb user=lmfdb password=lmfdb')
PRIMES=[2,13,29,41,43]
CONDUCTORS=sorted({3**a*7**b for a in range(4) for b in range(3) if 3**a*7**b>1})
class FetchError(RuntimeError):pass

def canonical(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def normalize(value:Any)->Any:
    if isinstance(value,Decimal):return int(value)
    if isinstance(value,tuple):return [normalize(x) for x in value]
    if isinstance(value,list):return [normalize(x) for x in value]
    if isinstance(value,dict):return {str(k):normalize(v) for k,v in value.items()}
    return value
def legendre(value:int,p:int)->int:
    value%=p
    if value==0:return 0
    symbol=pow(value,(p-1)//2,p)
    return -1 if symbol==p-1 else 1
def trace(ainvs:list[int],p:int)->int:
    if len(ainvs)!=5:raise FetchError(f'bad a-invariants: {ainvs}')
    a1,a2,a3,a4,a6=(int(v) for v in ainvs); points=1
    for x in range(p):
        linear=(a1*x+a3)%p; rhs=(x**3+a2*x*x+a4*x+a6)%p
        points+=1+legendre(linear*linear+4*rhs,p)
    return p+1-points
def main()->int:
    with psycopg.connect(DSN,connect_timeout=30) as connection:
        with connection.cursor() as cursor:
            cursor.execute('''
              SELECT DISTINCT ON (lmfdb_iso)
                     lmfdb_iso, lmfdb_label, conductor, ainvs, cm
              FROM ec_curvedata
              WHERE conductor=ANY(%s)
              ORDER BY lmfdb_iso, lmfdb_number
            ''',(CONDUCTORS,))
            rows=cursor.fetchall()
    records=[]
    for iso,label,conductor,ainvs,cm in rows:
        invariants=[int(v) for v in ainvs]
        traces={str(p):trace(invariants,p) for p in PRIMES if int(conductor)%p}
        records.append({'isogeny_class':iso,'representative_label':label,'conductor':int(conductor),'ainvs':invariants,'cm_discriminant':int(cm),'traces':traces})
    body=normalize({'schema_version':1,'status':'complete rational elliptic source inventory for conductors supported at 3 and 7 with exponents <=(3,2)','source':{'database':'LMFDB public SQL mirror','table':'ec_curvedata','one_representative_per_isogeny_class':True,'elliptic_curve_completeness_bound':500000},'candidate_conductors':CONDUCTORS,'trace_primes':PRIMES,'record_count':len(records),'records':records,'nonclaim':'this inventory eliminates only genuine rational base-change packets; a rational-coefficient Hilbert packet still requires a Galois-invariance/descent argument before this list applies'})
    output=dict(body);output['certificate_sha256']=canonical(body);json.dump(output,sys.stdout,sort_keys=True,indent=2);print();return 0
if __name__=='__main__':raise SystemExit(main())
