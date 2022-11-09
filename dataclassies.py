from dataclasses import dataclass


@dataclass
class EPG:
    id: int
    name: str
    start_at: int
    end_at: int
