"""Atomic application-file replacement with bounded Windows lock retries."""
import os
from pathlib import Path
import time
import uuid


def atomic_write_bytes(path: Path, content: bytes):
    for attempt in range(6):
        temporary = path.with_name(path.name + '.' + uuid.uuid4().hex[:12] + '.tmp')
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with temporary.open('xb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(.05 * 2 ** attempt)
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                # Cleanup must not replace the original write/replace error.
                pass
