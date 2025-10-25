from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict
import uuid

@dataclass
class NotificationMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    level: str = "INFO"  # INFO, WARN, ALERT, ERROR
    title: str = ""
    text: str = ""
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)
