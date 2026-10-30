#!/usr/bin/env python3
"""Publish a validated report archive into an operator-protected directory."""
import argparse
import ctypes
import errno
import io
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile

import usage_telemetry_contract as contract
import usage_telemetry_exports as exports

LIMIT = 64 * 1024 * 1024


def validate_archive(data):
    if not isinstance(data, bytes) or len(data) > LIMIT:
        raise ValueError('invalid archive')
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
            members = archive.getmembers()
            if [item.name for item in members] != list(exports._FILES.values()):
                raise ValueError('invalid archive members')
            content = {}
            for item in members:
                if not item.isfile() or item.size > LIMIT:
                    raise ValueError('invalid archive member')
                content[item.name] = archive.extractfile(item).read().decode('utf-8')
        report = contract.parse_json(content['report.json'])
        expected = exports.render_exports(report)
        if exports.archive_exports(expected) != data:
            raise ValueError('inconsistent archive')
    except (tarfile.TarError, UnicodeError, KeyError, AttributeError, OSError):
        raise ValueError('invalid archive') from None


def _check_location(directory):
    current = os.readlink('/proc/self/fd/' + str(directory))
    if not current.startswith('/') or current.endswith(' (deleted)'):
        raise ValueError('invalid report directory')
    log_root = os.environ.get('ORCHESTRAIL_LOG_ROOT') or str(Path(__file__).resolve().parents[1] / 'logs')
    roots = [os.path.realpath(os.path.join(log_root, 'usage', 'v1')),
             os.path.realpath(Path(__file__).resolve().parents[1] / 'logs' / 'usage' / 'v1')]
    if any(os.path.commonpath((current, root)) == root for root in roots):
        raise ValueError('invalid report directory')
    return current


def publish(directory, name, data):
    """Install exactly once; caller must protect the directory from relocation and mutation."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', name) or name in ('.', '..'):
        raise ValueError('invalid report name')
    if not stat.S_ISDIR(os.fstat(directory).st_mode):
        raise ValueError('invalid report directory')
    validate_archive(data)
    location = _check_location(directory)
    # O_TMPFILE has no directory entry while bytes are written. linkat creates
    # the final name atomically and never replaces an existing entry.
    descriptor = os.open('.', os.O_WRONLY | os.O_TMPFILE, 0o600, dir_fd=directory)
    try:
        remaining = memoryview(data)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError('archive write failed')
            remaining = remaining[written:]
        os.fsync(descriptor)
        libc = ctypes.CDLL(None, use_errno=True)
        linkat = libc.linkat
        linkat.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        linkat.restype = ctypes.c_int
        if _check_location(directory) != location:
            raise ValueError('report directory moved')
        if linkat(descriptor, b'', directory, os.fsencode(name), 0x1000):
            error = ctypes.get_errno()
            if error != errno.EEXIST:
                raise OSError(error, os.strerror(error))
            existing = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=directory)
            try:
                info = os.fstat(existing)
                if not stat.S_ISREG(info.st_mode) or info.st_size != len(data):
                    raise OSError('report revision conflict')
                with os.fdopen(existing, 'rb', closefd=False) as stream:
                    if stream.read(len(data) + 1) != data:
                        raise OSError('report revision conflict')
            finally:
                os.close(existing)
        os.fsync(directory)
    finally:
        os.close(descriptor)


def run_producer(command):
    """Collect bounded output and require a successful producer before publication."""
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL)
    try:
        data = process.stdout.read(LIMIT + 1)
        if len(data) > LIMIT:
            process.kill()
            process.wait()
            raise ValueError('archive exceeds limit')
        status = process.wait()
        if status == 2:
            raise ValueError('analysis failed')
        if status != 0:
            raise OSError('analysis failed')
        return data
    finally:
        process.stdout.close()
        if process.poll() is None:
            process.kill()
            process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory-fd', type=int, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--protected-directory-acknowledged', action='store_true')
    parser.add_argument('--corpus-manifest', required=True)
    parser.add_argument('--scenario', required=True)
    parser.add_argument('--authority', required=True)
    parser.add_argument('--authority-key', required=True)
    args = parser.parse_args()
    if args.directory_fd < 3 or not args.protected_directory_acknowledged:
        raise ValueError('protected directory authority required')
    command = [sys.executable, str(Path(__file__).with_name('usage-telemetry.py')),
               'analyze', '--corpus-manifest', args.corpus_manifest, '--scenario', args.scenario,
               '--authority', args.authority, '--authority-key', args.authority_key]
    publish(args.directory_fd, args.name, run_producer(command))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, TypeError, OverflowError, RecursionError):
        print('report publication: invalid input', file=sys.stderr)
        sys.exit(2)
    except OSError:
        print('report publication: input or output failure', file=sys.stderr)
        sys.exit(3)
