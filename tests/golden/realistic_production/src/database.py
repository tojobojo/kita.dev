"""Database layer simulation."""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Record:
    id: int
    data: dict


class InMemoryDB:
    """Simple in-memory database for testing."""

    def __init__(self):
        self._tables: Dict[str, List[Record]] = {}
        self._id_counter = 0

    def create_table(self, name: str) -> None:
        if name not in self._tables:
            self._tables[name] = []

    def insert(self, table: str, data: dict) -> int:
        self._id_counter += 1
        record = Record(id=self._id_counter, data=data)

        if table not in self._tables:
            self.create_table(table)

        self._tables[table].append(record)
        return record.id

    def find_by_id(self, table: str, record_id: int) -> Optional[Record]:
        if table not in self._tables:
            return None

        for record in self._tables[table]:
            if record.id == record_id:
                return record
        return None

    def find_all(self, table: str) -> List[Record]:
        return self._tables.get(table, [])

    def delete(self, table: str, record_id: int) -> bool:
        if table not in self._tables:
            return False

        for i, record in enumerate(self._tables[table]):
            if record.id == record_id:
                del self._tables[table][i]
                return True
        return False


# Global database instance
db = InMemoryDB()
