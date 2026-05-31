# Reporter Trust Score Implementation Summary

## Overview
Added a lightweight reporter trust mechanism that modifies report influence in aggregation while maintaining compatibility with the existing 10-minute rolling report window design.

---

## Changes Made

### 1. New SQLModel Tables

#### [app/models/reporter_profile.py](app/models/reporter_profile.py)
```python
class ReporterProfile(SQLModel, table=True):
    user_id: int = Field(primary_key=True)
    trust_score: float = 0.5
    last_updated: datetime
```
- Stores per-user trust scores
- Default trust = 0.5
- Last updated tracks profile modification time

#### [app/models/system_state.py](app/models/system_state.py)
```python
class SystemState(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: datetime
```
- Generic key-value store for system state
- Used to track last reconciliation timestamp
- Key: `"last_reconciliation_at"`

---

### 2. Updated Service Layer

#### [app/services/report_service.py](app/services/report_service.py)

**New Constants:**
```python
DEFAULT_REPORTER_TRUST = 0.5
TRUST_CORROBORATED_DELTA = 0.02
TRUST_CONTRADICTED_DELTA = -0.03
SYSTEM_STATE_LAST_RECONCILIATION_KEY = "last_reconciliation_at"
```

**New Helper Functions:**

1. **`_get_or_create_reporter_profile(user_id, session)`**
   - Fetches or creates a ReporterProfile
   - Used internally by trust lookup

2. **`get_or_create_reporter_trust(user_id, session)`**
   - Returns trust_score as float
   - Creates profile with default trust if missing
   - **Public API** for trust lookup

3. **`_get_system_state_timestamp(session, key)`**
   - Retrieves datetime from SystemState by key
   - Returns None if not set

4. **`_set_system_state_timestamp(session, key, value)`**
   - Stores datetime in SystemState
   - Creates or updates entry

**New Reconciliation Functions:**

1. **`reconcile_reporter_trust(session)`**
   - Fetches reports outside REPORT_WINDOW_MINUTES
   - For each report, compares against majority consensus in same edge/window
   - Updates trust based on CORROBORATED (+0.02) or CONTRADICTED (-0.03)
   - Clamps trust between 0.0–1.0
   - Updates last_reconciliation_at timestamp
   - **Called on demand, not scheduled**

2. **`maybe_reconcile_reporter_trust(session)`**
   - Gate function: runs reconciliation if last run > 5–10 minutes ago
   - Lazy trigger to avoid excessive reconciliation runs

**Modified Aggregation:**

In `compute_edge_status_per_transport()`:
- **Old:** `weight = location_weight * time_decay(report.created_at)`
- **New:** `weight = location_weight * time_decay(report.created_at) * reporter_trust`

Changes:
- Fetches reporter_trust via `get_or_create_reporter_trust(user_id, session)`
- Caches trust scores in `trust_cache` to avoid duplicate lookups
- Trust multiplier downweights reports from low-trust reporters

**Modified `get_status()`:**
- Calls `maybe_reconcile_reporter_trust(session)` as first step
- Lazy reconciliation triggers before status aggregation

---

### 3. Database Migration

#### [alembic/versions/9c21c3bb1f47_add_reporter_trust_and_system_state.py](alembic/versions/9c21c3bb1f47_add_reporter_trust_and_system_state.py)

Alembic migration that:
- Creates `reporter_profile` table
- Creates `system_state` table
- Establishes indexes for efficient lookups

---

### 4. Package Exports

#### [app/models/__init__.py](app/models/__init__.py)
- Added `ReporterProfile` to imports and `__all__`
- Added `SystemState` to imports and `__all__`

---

## Design Constraints Maintained

✓ **Minimal changes** – Only service layer + two new models  
✓ **No background workers or cron jobs** – Reconciliation is lazy/on-demand  
✓ **No source_type or trust_outcome fields** – Kept model simple  
✓ **No correct_reports/wrong_reports counters** – Simple signature matching only  
✓ **Compatible with 10-minute window** – Reconciliation respects existing window logic  
✓ **Existing confidence/entropy logic untouched** – Only weight multiplier changed  
✓ **API structure unchanged** – No endpoint signature changes  

---

## Integration Flow

```
1. User calls get_status(edge_id, session)
   ↓
2. maybe_reconcile_reporter_trust() checks if reconciliation needed
   ↓
3. If > 5-10 min since last reconciliation:
   - reconcile_reporter_trust() processes old reports
   - Compares each against majority consensus
   - Updates trust scores (+0.02 or -0.03)
   - Clamps to [0.0, 1.0]
   ↓
4. get_recent_reports() fetches 10-minute window
   ↓
5. compute_edge_status_per_transport() aggregates:
   - For each report: trust = get_or_create_reporter_trust(user_id)
   - weight = location_score * time_decay * trust
   - Uses weighted votes for majority queue_level/availability
   ↓
6. Return aggregated status with trust-weighted confidence
```

---

## Default Behavior

- New reporters start with trust_score = 0.5
- Trust multiplier ranges 0.0–1.0
- Low-trust reports downweight but don't eliminate
- Reconciliation runs automatically every 5–10 minutes (lazy)
- No API changes – fully backward compatible

---

## Testing

[tests/test_reporter_trust.py](tests/test_reporter_trust.py) includes:
- Profile creation test
- Trust lookup test  
- Weight multiplier validation
- Reconciliation corroboration test

Run: `python tests/test_reporter_trust.py`

---

## Files Changed

| File | Type | Status |
|------|------|--------|
| [app/models/reporter_profile.py](app/models/reporter_profile.py) | New | ✓ Created |
| [app/models/system_state.py](app/models/system_state.py) | New | ✓ Created |
| [app/models/__init__.py](app/models/__init__.py) | Modified | ✓ Updated |
| [app/services/report_service.py](app/services/report_service.py) | Modified | ✓ Updated |
| [alembic/versions/9c21c3bb1f47_add_reporter_trust_and_system_state.py](alembic/versions/9c21c3bb1f47_add_reporter_trust_and_system_state.py) | New | ✓ Created |
| [tests/test_reporter_trust.py](tests/test_reporter_trust.py) | New | ✓ Created |

---

## Next Steps

1. Run Alembic migration:
   ```bash
   alembic upgrade head
   ```

2. Test aggregation endpoint:
   ```bash
   python tests/test_reporter_trust.py
   ```

3. Deploy – no API changes, fully backward compatible
