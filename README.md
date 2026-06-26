# dbzero-modelkit

Reusable model primitives for projects that store Python objects with
[dbzero](https://docs.dbzero.io/).

`dbzero-modelkit` provides small, focused building blocks for common model patterns:
sparse calendars, active-date windows, month-indexed storage, multilingual strings,
FIFO queues, and tag-based object locks. The package is application-neutral and is
intended to be imported by any Python project using dbzero.

## Installation

```bash
pip install dbzero-modelkit
```

Requirements:

- Python 3.9 or newer
- One db backend extra:
  - `dbzero-modelkit[dbzero]` for `dbzero>=0.4.0`
  - `dbzero-modelkit[dbzero-pro]` for `dbzero-pro>=0.3.3`

## Included Models

- `ActiveBase` and `ActiveIndex` for objects that are active only within a date or datetime range.
- `Calendar`, `MonthCalendar`, `get_month_index`, and `get_date_from_month_index` for sparse date-based values.
- `LanguageCode` and `ML_String` for primary text values with optional translations.
- `FiFoQueue` and `FQ_Item` for dbzero-backed FIFO queues.
- `MonthStore` for one-object-per-month storage with lazy item creation.
- `ObjectLock` for temporary tag-based locking of dbzero objects.

## Quick Start

Initialize dbzero before creating or loading dbzero-backed model objects:

```python
from datetime import date

import dbzero as db0

from dbzero_modelkit import Calendar, FiFoQueue

db0.init("./db0_data", read_write=True)
db0.open("main", "rw")

calendar = Calendar(base_year=2026)
calendar.set(date(2026, 1, 1), "available")

queue = FiFoQueue()
queue.push_back(kind="email", recipient="user@example.test")

assert calendar.get(date(2026, 1, 1)) == "available"
assert queue.pop_front(1) == [
    {"kind": "email", "recipient": "user@example.test"},
]

db0.close()
```
