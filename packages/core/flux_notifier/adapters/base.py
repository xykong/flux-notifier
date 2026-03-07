from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from flux_notifier.schema import NotificationPayload


@dataclass
class SendResult:
    success: bool
    adapter: str
    message: str = ""
    response_url: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


class AdapterBase(ABC):
    name: str = ""

    @abstractmethod
    async def send(self, payload: NotificationPayload) -> SendResult:
        ...

    async def health_check(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
