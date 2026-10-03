"""Fail-closed, process-scoped output locks on Unix and Windows."""
from contextlib import contextmanager
import errno
import hashlib
import os


@contextmanager
def locked_output(destination):
    if destination.is_symlink():
        raise ValueError('Output destination must not be a symlink.')
    # Keep lock state outside generated output so a refused reconciliation leaves
    # the destination untouched. Resolve aliases to the same persistent lock inode;
    # never unlink it on release, which could let concurrent processes lock different files.
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    identity = hashlib.sha256(os.path.normcase(str(destination)).encode()).hexdigest()
    lock = destination.parent / f'.factory-build-{identity}.lock'
    if lock.is_symlink():
        raise ValueError('Output lock must not be a symlink.')
    handle = None
    acquired = False
    locking = False
    try:
        flags = os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0)
        handle = os.fdopen(os.open(lock, flags, 0o600), 'r+b')
        if os.name == 'nt':
            import msvcrt
            if os.fstat(handle.fileno()).st_size == 0:
                handle.write(b'0')
                handle.flush()
            handle.seek(0)
            locking = True
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            locking = True
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        acquired = True
    except (OSError, ImportError) as error:
        if handle:
            handle.close()
        if locking and isinstance(error, OSError) and error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
            raise ValueError(f'Output {destination} is locked by another build process. No output was reconciled.') from error
        raise ValueError(f'Cannot acquire output lock for {destination}: {error}. No output was reconciled.') from error
    try:
        yield
    finally:
        if acquired:
            try:
                if os.name == 'nt':
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()
