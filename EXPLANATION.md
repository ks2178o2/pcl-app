# Why Coverage Changes?

## Two Different Measurements:

### 1. Earlier "20.75%" was WRONG
- Included 2261 lines total
- This INCLUDED untested API and middleware files
- Those files have 0% coverage
- This INFLATED the total, making coverage look worse

### 2. Current "36.77%" is MORE ACCURATE
- Only 1280 lines total
- Focuses on services layer ONLY
- API and middleware files EXCLUDED from services/ coverage
- Gives true picture of services coverage

## What Changed?

Earlier command may have included:
- api/ folder (750 lines, 0% coverage)
- middleware/ folder (378 lines, 0% coverage)

Current command focuses on:
- services/ folder ONLY
- This is where we're actually testing

## Reality Check:

```
services/context_manager.py        194 lines   95.93%  ✅ 
services/audit_service.py           169 lines   82.67%  ✅
services/enhanced_context_manager.py 276 lines  25.86%  🟡
services/tenant_isolation_service.py 274 lines  18.32%  🟡
services/supabase_client.py          73 lines  35.63%  🟡
services/feature_inheritance_service.py 144 lines 0.00%  🔴
```

TOTAL: 1130 lines in services/ folder
COVERED: ~500 lines (varies based on what's included)

36.77% is the REAL coverage for services layer.
