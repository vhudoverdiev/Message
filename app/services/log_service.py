from sqlalchemy.orm import Session

from app.models.log_entry import LogEntry


def write_log(db: Session, action: str, details: str = '', level: str = 'INFO', user_id: int | None = None) -> None:
    entry = LogEntry(level=level, action=action, details=details, user_id=user_id)
    db.add(entry)
    db.commit()
