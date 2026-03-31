"""In-memory database for local development and testing.

Implements the same chained query interface as the Supabase Python client
so the engines and routes work without a real database connection.
"""

from datetime import datetime, timezone
from uuid import uuid4


class _Result:
    def __init__(self, data):
        self.data = data


class _QueryBuilder:
    def __init__(self, store: dict, table_name: str):
        self._store = store
        self._table = table_name
        self._filters: list[tuple[str, str, str]] = []
        self._order_col: str | None = None
        self._order_desc: bool = False
        self._limit_n: int | None = None
        self._range_start: int | None = None
        self._range_end: int | None = None
        self._select_cols: str = "*"
        self._insert_data: dict | None = None
        self._update_data: dict | None = None
        self._maybe_single: bool = False

    def select(self, cols: str = "*"):
        self._select_cols = cols
        return self

    def insert(self, data: dict):
        row = {**data}
        if "id" not in row:
            row["id"] = str(uuid4())
        if "created_at" not in row:
            row["created_at"] = datetime.now(timezone.utc).isoformat()
        self._store.setdefault(self._table, []).append(row)
        self._insert_data = row
        return self

    def update(self, data: dict):
        self._update_data = data
        return self

    def eq(self, col: str, val):
        self._filters.append((col, "eq", str(val)))
        return self

    def neq(self, col: str, val):
        self._filters.append((col, "neq", str(val)))
        return self

    def order(self, col: str, desc: bool = False):
        self._order_col = col
        self._order_desc = desc
        return self

    def limit(self, n: int):
        self._limit_n = n
        return self

    def range(self, start: int, end: int):
        self._range_start = start
        self._range_end = end
        return self

    def maybe_single(self):
        self._maybe_single = True
        return self

    def execute(self) -> _Result:
        if self._insert_data is not None:
            return _Result([self._insert_data])

        if self._update_data is not None:
            rows = self._apply_filters()
            for row in rows:
                row.update(self._update_data)
            return _Result(rows)

        if self._maybe_single:
            rows = self._apply_filters()
            return _Result(rows[0] if rows else None)

        rows = self._apply_filters()

        if self._order_col:
            rows.sort(
                key=lambda r: r.get(self._order_col, ""),
                reverse=self._order_desc,
            )

        if self._range_start is not None and self._range_end is not None:
            rows = rows[self._range_start : self._range_end + 1]

        if self._limit_n is not None:
            rows = rows[: self._limit_n]

        return _Result(rows)

    def _apply_filters(self) -> list[dict]:
        rows = list(self._store.get(self._table, []))
        for col, op, val in self._filters:
            if op == "eq":
                rows = [r for r in rows if str(r.get(col)) == val]
            elif op == "neq":
                rows = [r for r in rows if str(r.get(col)) != val]
        return rows


class InMemoryDB:
    """Drop-in replacement for Supabase client using in-memory dicts."""

    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    def table(self, name: str) -> _QueryBuilder:
        return _QueryBuilder(self._store, name)

    def dump(self) -> dict:
        """Return all stored data (useful for debugging)."""
        return {k: list(v) for k, v in self._store.items()}
