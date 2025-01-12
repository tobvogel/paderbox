import os
import tempfile
import contextlib

from paderbox.io.path_utils import normalize_path


__all__ = [
    'open_atomic',
    'write_text_atomic',
    'write_bytes_atomic',
]


@contextlib.contextmanager
def open_atomic(file, mode, *args, force=False, **kwargs):
    """
    Produce a tempfile aside to the desired file (same filesystem).
    Overwrite the file on successful context (except force is True than always).

    This function is inspiered from:
    # https://stackoverflow.com/questions/2333872/atomic-writing-to-file-with-python

    For replace alternative see
    # http://code.activestate.com/recipes/579097-safely-and-atomically-write-to-a-file/


    Note:
        This function allows to overwrite a file, while another process still
        read the file. The other process keep a file pointer to the original
        file. The original file is removed from the filesystem when nobody
        reads the file. This is a nice property known from Makefiles.

    Note:
        A file that is written with this function can only be read, when it is
        fully written (i.e. the context is left).

    Examples:

    >>> import sys, pytest
    >>> if sys.platform.startswith('win'):
    ...     pytest.skip('this doctest does not work on Windows, '
    ...                 'accessing an opened file is not possible')

    Procure a file with some content
    >>> from paderbox.io.cache_dir import get_cache_dir
    >>> file = get_cache_dir() / 'tmp.io.txt'
    >>> with open(file, 'w') as f:
    ...     f.write('test\\nbla')
    8
    >>> with open(file, 'r') as f:
    ...     print(f.read())
    test
    bla

    Read the file and write to the file the same content
    (with open_atomic no problem)
    >>> with open(file, 'r') as src:
    ...     with open_atomic(file, 'w') as f:
    ...         for line in src:
    ...             f.write(line)
    ...     src.seek(0)
    ...     with open_atomic(file, 'w') as f:
    ...         for line in src:
    ...             f.write(line + 'second write\\n')
    5
    3
    0
    18
    16
    >>> with open(file, 'r') as f:
    ...     print(f.read())
    test
    second write
    blasecond write
    <BLANKLINE>

    Read the file and write to the file the same content
    (with open this does not work)
    >>> with open(file, 'r') as src:
    ...     with open(file, 'w') as dst:
    ...         for line in src:
    ...             f.write(line)
    >>> with open(file, 'r') as f:
    ...     print(f.read())
    <BLANKLINE>
    >>> with open_atomic(file, 'w') as f:
    ...     f.write('test\\nbla')
    ...     f.write('test\\nbla')
    8
    8
    >>> with open(file, 'r') as f:
    ...     print(f.read())
    test
    blatest
    bla

    When an exception occurs do not write anything (except force is True)
    >>> with open_atomic(file, 'w') as f:
    ...     f.write('sdkfg\\nbla')
    ...     raise Exception
    Traceback (most recent call last):
    ...
    Exception
    >>> with open(file, 'r') as f:
    ...     print(f.read())
    test
    blatest
    bla
    >>> with open_atomic(file, 'w', force=True) as f:
    ...     f.write('sdkfg\\nbla')
    ...     raise Exception
    Traceback (most recent call last):
    ...
    Exception
    >>> with open(file, 'r') as f:
    ...     print(f.read())
    sdkfg
    bla

    >>> with open_atomic(file, 'w') as f:
    ...     print('Name:', f.name)  # doctest: +ELLIPSIS
    Name: ...tmp.io.txt...
    """
    file = normalize_path(file, as_str=True, allow_fd=False)

    assert 'w' in mode, mode

    if os.name == 'nt':
        tmp_f = tempfile.NamedTemporaryFile(
                    mode, *args, **kwargs, delete=False, prefix=file, dir=os.getcwd()
            )
        fname = tmp_f.name

        def close_and_remove():
            tmp_f.close()
            os.unlink(fname)
        
        def cleanup():
                tmp_f.flush()
                os.fsync(tmp_f.fileno())
                # open files cannot be accessed
                tmp_f.close()
                os.replace(fname, file)
        
        skip_close = False

        try:
            yield tmp_f
            # skipped if exception is raised
            if not force:
                skip_close = True
                cleanup()
        except:
            # clean up by removing temp file if exception is raised -> no partial write
            skip_close = True
            close_and_remove()
            raise
        finally:
            #  force write, may raise error
            if force:
                cleanup()
            # close file
            if not skip_close:
                close_and_remove()
    else:
        with tempfile.NamedTemporaryFile(
            mode, *args, **kwargs, prefix=file, dir=os.getcwd()
        ) as tmp_f:
            def cleanup():
                tmp_f.flush()
                os.fsync(tmp_f.fileno())
                # os.rename(tmp_f.name, file)  # fails if dst exists
                os.replace(tmp_f.name, file)

                # Disable NamedTemporaryFile.close(), because the file was renamed.
                tmp_f.delete = False
                tmp_f._closer.delete = False
            try:
                yield tmp_f
                if not force:
                    cleanup()
            finally:
                if force:
                    cleanup()


def write_text_atomic(data: str, path):
    """
    Writes the data in text mode to path as an atomic operation.

    Args:
        data: str
        path: str or pathlib.Path
    """
    # Path.write_text()
    with open_atomic(path, 'w') as fd:
        fd.write(data)


def write_bytes_atomic(data: bytes, path):
    """
    Writes the data in binary mode to path as an atomic operation.

    Args:
        data: str
        path: str or pathlib.Path
    """
    # Path.write_bytes()
    with open_atomic(path, 'wb') as fd:
        fd.write(data)
