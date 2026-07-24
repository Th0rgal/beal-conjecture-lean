# Level-91125 fixed-7 LMFDB inventory query

This read-only query joins `hmf_forms` and `hmf_hecke` for every stored parallel-weight-2 packet over `Q(sqrt(5))` at level norm `91125`:

[Run the exact LMFDB SQL query](https://mcp.lmfdb.org/sql?sql=SELECT+f.label%2Cf.level_norm%2Cf.level_ideal%2Cf.dimension%2Cf.%22is_CM%22%2Cf.is_base_change%2Ch.hecke_polynomial%2Ch.hecke_eigenvalues+FROM+hmf_forms+f+JOIN+hmf_hecke+h+USING%28label%29+WHERE+f.field_label%3D%272.2.5.1%27+AND+f.level_norm%3D91125+AND+f.parallel_weight%3D2+ORDER+BY+f.label&limit=200)

Missing records are not interpreted as arithmetic elimination; the expected packet count is 112.
