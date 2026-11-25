"""Deterministic gzip-compressed tarball of the schema bundle.

The release asset and its checksum must be the same on every platform and in
every build. The archive therefore fixes everything that a file system would
otherwise decide:

- The member order is the sorted order of the bundle manifest.
- The member metadata is fixed: no modification time, no owner, and one mode.
- The gzip header carries no modification time and no file name.
- The compression level is fixed.

The archive keeps the content of every file as it is. The publisher writes the
published bundle with the identity of the release tag, and the release lane
archives that directory, so the release asset matches the tagged commit byte
for byte.

See `docs/decisions/ADR-0022-release-artifacts-schema-distribution-and-response-policy.md`.
"""

from __future__ import annotations

import struct
import tarfile
import zlib
from io import BytesIO
from pathlib import Path

from typcast_publish.errors import PublishError

ARCHIVE_PREFIX = "typcast-schemas"
COMPRESSION_LEVEL = 9
FILE_MODE = 0o644
GZIP_HEADER = b"\x1f\x8b\x08\x00" + struct.pack("<I", 0) + b"\x02\xff"


def gzip_stream(payload: bytes) -> bytes:
    """Returns the gzip stream of a payload.

    The header is written by hand, so the bytes depend only on the payload
    and not on the Python version or on the clock.
    """
    compressor = zlib.compressobj(
        COMPRESSION_LEVEL,
        zlib.DEFLATED,
        -zlib.MAX_WBITS,
    )
    body = compressor.compress(payload) + compressor.flush()
    trailer = struct.pack("<I", zlib.crc32(payload) & 0xFFFFFFFF)
    trailer += struct.pack("<I", len(payload) & 0xFFFFFFFF)
    return GZIP_HEADER + body + trailer


def tar_stream(members: list[tuple[str, bytes]]) -> bytes:
    """Returns the tar archive of the given members."""
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.GNU_FORMAT) as archive:
        for name, payload in members:
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            info.mtime = 0
            info.mode = FILE_MODE
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.type = tarfile.REGTYPE
            archive.addfile(info, BytesIO(payload))
    return buffer.getvalue()


def archive_members(
    sources: list[tuple[str, Path]],
    prefix: str = ARCHIVE_PREFIX,
) -> list[tuple[str, bytes]]:
    """Returns the name and the content of every member of the archive.

    Every source is a relative path inside the bundle and the path of the
    file that holds it.
    """
    if not sources:
        raise PublishError("the bundle manifest is empty")

    members: list[tuple[str, bytes]] = []
    for relative_path, path in sorted(sources):
        normalized = relative_path.replace("\\", "/").strip("/")
        if not normalized or ".." in normalized.split("/"):
            raise PublishError(f"invalid bundle path: {relative_path}")
        if not path.is_file():
            raise PublishError(
                f"schema bundle is incomplete: {relative_path} is missing"
            )
        members.append((f"{prefix}/{normalized}", path.read_bytes()))
    return members


def bundle_sources(bundle_dir: Path, manifest: list[str]) -> list[tuple[str, Path]]:
    """Returns the source of every file of a bundle directory."""
    if not bundle_dir.is_dir():
        raise PublishError(f"schema bundle not found: {bundle_dir}")
    if not manifest:
        raise PublishError("the bundle manifest is empty")
    return [
        (relative_path, bundle_dir / relative_path)
        for relative_path in sorted(manifest)
    ]


def write_archive(
    sources: list[tuple[str, Path]],
    output: Path,
    prefix: str = ARCHIVE_PREFIX,
) -> list[str]:
    """Writes the deterministic archive and returns the member names."""
    members = archive_members(sources, prefix)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(gzip_stream(tar_stream(members)))
    return [name for name, _ in members]


def write_bundle_archive(
    bundle_dir: Path,
    manifest: list[str],
    output: Path,
    prefix: str = ARCHIVE_PREFIX,
) -> list[str]:
    """Writes the archive of a bundle directory."""
    return write_archive(bundle_sources(bundle_dir, manifest), output, prefix)


def bundle_archive_bytes(bundle_dir: Path, manifest: list[str]) -> bytes:
    """Returns the deterministic archive of a bundle directory.

    The bytes are the archive that the release asset carries. Two bundle
    directories with the same content produce the same bytes.
    """
    members = archive_members(bundle_sources(bundle_dir, manifest))
    return gzip_stream(tar_stream(members))
