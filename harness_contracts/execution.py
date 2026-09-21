from __future__ import annotations

import hashlib
import subprocess
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

CHUNK_SIZE = 1024 * 1024
SHA256_LENGTH = 64


class ContractViolation(ValueError):
    """Raised when an execution contract cannot be satisfied safely."""


class OptionalCapabilityUnavailable(RuntimeError):
    """Raised by an optional stage when its scoped dependency is unavailable."""


class StageOutcome(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class InputSnapshot:
    path: str
    size: int
    sha256: str

    def __post_init__(self) -> None:
        _validate_file_record(self.path, self.size, self.sha256)

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "size": self.size, "sha256": self.sha256}


@dataclass(frozen=True)
class InputRecord:
    path: str
    before: InputSnapshot
    after: InputSnapshot | None = None

    @property
    def unchanged(self) -> bool:
        return self.after is not None and self.before == self.after

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "before": self.before.to_dict(),
            "after": self.after.to_dict() if self.after else None,
            "unchanged": self.unchanged,
        }


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    size: int
    sha256: str
    committed: bool = True

    def __post_init__(self) -> None:
        _validate_relative_path(self.path)
        _validate_file_record(self.path, self.size, self.sha256)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "size": self.size,
            "sha256": self.sha256,
            "committed": self.committed,
        }


@dataclass(frozen=True)
class Provenance:
    tool: str
    runtime: str
    configuration: Mapping[str, object] = field(default_factory=dict)
    dependencies: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tool.strip():
            raise ContractViolation("provenance.tool must not be empty")
        if not self.runtime.strip():
            raise ContractViolation("provenance.runtime must not be empty")

    def to_dict(self) -> dict[str, object]:
        return {
            "tool": self.tool,
            "runtime": self.runtime,
            "configuration": dict(self.configuration),
            "dependencies": dict(self.dependencies),
        }


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration_seconds: float

    @property
    def succeeded(self) -> bool:
        return not self.timed_out and self.returncode == 0

    def to_dict(self) -> dict[str, object]:
        return {
            "argv": list(self.argv),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "timed_out": self.timed_out,
            "duration_seconds": self.duration_seconds,
            "succeeded": self.succeeded,
        }


@dataclass(frozen=True)
class StageResult:
    stage: str
    outcome: StageOutcome
    inputs: tuple[InputRecord, ...] = ()
    artifacts: tuple[ArtifactRecord, ...] = ()
    provenance: Provenance | None = None
    command: CommandResult | None = None
    diagnostics: tuple[str, ...] = ()
    reason: str | None = None

    def validate(self) -> None:
        if not self.stage.strip():
            raise ContractViolation("stage name must not be empty")
        if self.outcome is StageOutcome.COMPLETE:
            if self.provenance is None:
                raise ContractViolation("complete stage must include execution provenance")
            if any(not record.unchanged for record in self.inputs):
                raise ContractViolation("complete stage has unverified or mutated inputs")
            if self.command is not None and not self.command.succeeded:
                raise ContractViolation("complete stage has a failed or timed-out command")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "stage": self.stage,
            "outcome": self.outcome.value,
            "inputs": [record.to_dict() for record in self.inputs],
            "artifacts": [record.to_dict() for record in self.artifacts],
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "command": self.command.to_dict() if self.command else None,
            "diagnostics": list(self.diagnostics),
            "reason": self.reason,
        }


def _validate_relative_path(path: str) -> None:
    candidate = Path(path)
    if not path or candidate.is_absolute() or ".." in candidate.parts:
        raise ContractViolation(f"path must be relative and stay inside its root: {path!r}")


def _validate_file_record(path: str, size: int, sha256: str) -> None:
    if not path:
        raise ContractViolation("file record path must not be empty")
    if size < 0:
        raise ContractViolation(f"file record size must be non-negative: {path!r}")
    if len(sha256) != SHA256_LENGTH or any(char not in "0123456789abcdef" for char in sha256):
        raise ContractViolation(f"file record must contain a lowercase SHA-256 digest: {path!r}")


def _hash_file(path: Path) -> tuple[int, str]:
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ContractViolation(f"file changed while hashing: {path}")
    return after.st_size, digest.hexdigest()


def _snapshot(path: Path, label: str) -> InputSnapshot:
    if path.is_symlink() or not path.is_file():
        raise ContractViolation(f"input is not a regular file: {path}")
    size, digest = _hash_file(path)
    return InputSnapshot(path=label, size=size, sha256=digest)


def capture_input(path: Path, *, label: str | None = None) -> InputRecord:
    """Capture the pre-stage identity of an input file."""

    resolved = path.expanduser().resolve()
    display_path = label or resolved.as_posix()
    return InputRecord(path=display_path, before=_snapshot(resolved, display_path))


def verify_input(record: InputRecord, path: Path) -> InputRecord:
    """Attach an after-stage snapshot without hiding input mutation."""

    after = _snapshot(path.expanduser().resolve(), record.path)
    return InputRecord(path=record.path, before=record.before, after=after)


def create_run_root(parent: Path, *, prefix: str = "run") -> Path:
    """Create a unique run directory and refuse accidental reuse of an existing path."""

    resolved_parent = parent.expanduser().resolve()
    resolved_parent.mkdir(parents=True, exist_ok=True)
    for _ in range(10):
        candidate = resolved_parent / f"{prefix}-{uuid.uuid4().hex}"
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate
    raise ContractViolation(f"could not allocate a unique run root below {resolved_parent}")


def _safe_artifact_path(run_root: Path, relative_path: str) -> tuple[Path, str]:
    _validate_relative_path(relative_path)
    root = run_root.expanduser().resolve()
    if not root.is_dir():
        raise ContractViolation(f"run root is not a directory: {root}")
    relative = Path(relative_path)
    candidate = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ContractViolation(f"artifact path contains a symlink: {relative_path!r}")
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ContractViolation(f"artifact path escapes run root: {relative_path!r}") from error
    return candidate, relative.as_posix()


def describe_artifact(run_root: Path, relative_path: str) -> ArtifactRecord:
    """Hash a regular artifact only after enforcing the run-root and link boundaries."""

    path, normalized_path = _safe_artifact_path(run_root, relative_path)
    if path.is_symlink() or not path.is_file():
        raise ContractViolation(f"artifact is not a regular file: {relative_path!r}")
    if path.stat().st_nlink != 1:
        raise ContractViolation(f"artifact must not be a hard link: {relative_path!r}")
    size, digest = _hash_file(path)
    return ArtifactRecord(path=normalized_path, size=size, sha256=digest)


def verify_artifact(record: ArtifactRecord, run_root: Path) -> ArtifactRecord:
    """Re-hash a published artifact immediately before accepting its record."""

    current = describe_artifact(run_root, record.path)
    if current != record:
        raise ContractViolation(f"artifact changed after publication: {record.path!r}")
    return current


def run_external(
    argv: Sequence[str],
    *,
    timeout_seconds: float,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> CommandResult:
    """Run an external command with an argument list, timeout, and captured diagnostics."""

    command = tuple(argv)
    if not command or any(not argument for argument in command):
        raise ContractViolation("external command argv must contain non-empty arguments")
    if timeout_seconds <= 0:
        raise ContractViolation("external command timeout must be positive")

    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=str(cwd) if cwd else None,
        env=dict(env) if env is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        timed_out = False
    except subprocess.TimeoutExpired as error:
        process.kill()
        stdout, stderr = process.communicate()
        stdout = _text_output(error.stdout, fallback=stdout)
        stderr = _text_output(error.stderr, fallback=stderr)
        timed_out = True
    return CommandResult(
        argv=command,
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        duration_seconds=time.monotonic() - started,
    )


def _text_output(value: str | bytes | None, *, fallback: str) -> str:
    if value is None:
        return fallback
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def run_optional_stage(
    stage: str,
    available: bool,
    action: Callable[[], StageResult],
    *,
    unavailable_reason: str,
) -> StageResult:
    """Run an optional capability without turning its absence into a global preflight failure."""

    if not available:
        return StageResult(
            stage=stage,
            outcome=StageOutcome.PARTIAL,
            diagnostics=(unavailable_reason,),
            reason="optional capability unavailable",
        )
    try:
        return action()
    except OptionalCapabilityUnavailable as error:
        return StageResult(
            stage=stage,
            outcome=StageOutcome.PARTIAL,
            diagnostics=(str(error),),
            reason="optional capability unavailable",
        )
