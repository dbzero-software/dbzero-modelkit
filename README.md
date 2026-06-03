# dbzero-modelkit

Reusable dbzero-backed model utilities copied from Selltime workspace projects.

This package currently contains standalone copies of common data-model helpers only. It does not yet replace implementations in `selltime`, `statek`, or `kangal`; integration into those projects is planned as separate follow-up work.

## Included Models

- `ActiveBase` and `ActiveIndex` for active-window objects.
- `Calendar`, `MonthCalendar`, `get_month_index`, and `get_date_from_month_index` for sparse date calendars.
- `LanguageCode` and `ML_String` for multilingual strings.
- `FiFoQueue` and `FQ_Item` for dbzero-backed FIFO queues.
- `MonthStore` for sparse month-indexed object storage.
- `ObjectLock` for tag-based object locking.

## Testing

Run tests from this directory:

```bash
python3 -m pytest -q
```
