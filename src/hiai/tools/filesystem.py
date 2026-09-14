"""Filesystem tools for safe file operations within a project root."""

from __future__ import annotations

import os
from pathlib import Path

from hiai.constants import IGNORED_DIRS, MAX_FILE_READ_SIZE, MAX_LIST_FILES, MAX_SEARCH_RESULTS
from hiai.exceptions import FileReadError, FileWriteError, PathSecurityError
from hiai.models import ToolResult
from hiai.permissions import check_path_safety, is_sensitive
from hiai.utils.paths import match_ignored, resolve_safe_path


class FileSystemTools:
    """Safe filesystem operations within a project root."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def _resolve(self, path: str) -> Path:
        """Resolve and validate a path within the project root."""
        try:
            return resolve_safe_path(self.project_root, path)
        except ValueError as e:
            raise PathSecurityError(str(e)) from e

    def read_file(self, path: str) -> ToolResult:
        """Read a UTF-8 text file."""
        target = self._resolve(path)

        if not target.exists():
            return ToolResult(
                status="error",
                path=path,
                message=f"File not found: {path}",
            )

        if target.is_dir():
            return ToolResult(
                status="error",
                path=path,
                message=f"Path is a directory, not a file: {path}",
            )

        try:
            size = target.stat().st_size
        except OSError as e:
            return ToolResult(
                status="error",
                path=path,
                message=f"Cannot stat file: {e}",
            )

        if size > MAX_FILE_READ_SIZE:
            return ToolResult(
                status="error",
                path=path,
                message=f"File too large ({size} bytes). Max: {MAX_FILE_READ_SIZE}",
            )

        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ToolResult(
                status="error",
                path=path,
                message="File is not valid UTF-8 text (may be binary).",
            )
        except OSError as e:
            return ToolResult(
                status="error",
                path=path,
                message=f"Read error: {e}",
            )

        rel = str(target.relative_to(self.project_root))
        return ToolResult(
            status="success",
            path=rel,
            content=content,
            bytes=len(content.encode("utf-8")),
        )

    def write_file(self, path: str, content: str) -> ToolResult:
        """Write a UTF-8 text file (caller must handle permission prompting)."""
        target = self._resolve(path)
        is_new = not target.exists()

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return ToolResult(
                status="error",
                path=path,
                message=f"Cannot create parent directories: {e}",
            )

        try:
            data = content.encode("utf-8")
        except UnicodeEncodeError as e:
            return ToolResult(
                status="error",
                path=path,
                message=f"Encoding error: {e}",
            )

        if len(data) > 2_000_000:
            return ToolResult(
                status="error",
                path=path,
                message=f"Content too large ({len(data)} bytes). Max: 2MB.",
            )

        try:
            tmp_path = target.with_suffix(target.suffix + ".hiai_tmp")
            tmp_path.write_text(content, encoding="utf-8")
            tmp_path.replace(target)
        except OSError as e:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            return ToolResult(
                status="error",
                path=path,
                message=f"Write error: {e}",
            )

        rel = str(target.relative_to(self.project_root))
        op = "created" if is_new else "updated"
        return ToolResult(
            status="written",
            path=rel,
            bytes=len(data),
            operation=op,
        )

    def list_files(self, path: str = ".", recursive: bool = True) -> ToolResult:
        """List files in a directory."""
        target = self._resolve(path)

        if not target.exists():
            return ToolResult(
                status="error",
                path=path,
                message=f"Directory not found: {path}",
            )

        if not target.is_dir():
            return ToolResult(
                status="error",
                path=path,
                message=f"Not a directory: {path}",
            )

        files: list[str] = []

        if recursive:
            for dirpath, dirnames, filenames in os.walk(target):
                dirnames[:] = [d for d in dirnames if not match_ignored(d)]

                rel_dir = str(Path(dirpath).relative_to(self.project_root))

                for d in sorted(dirnames):
                    full = os.path.join(dirpath, d)
                    rel = str(Path(full).relative_to(self.project_root))
                    files.append(f"{rel}/")
                    if len(files) >= MAX_LIST_FILES:
                        return ToolResult(
                            status="truncated",
                            path=path,
                            files=files,
                            message=f"Results truncated at {MAX_LIST_FILES} entries",
                        )

                for f in sorted(filenames):
                    rel = str(Path(os.path.join(dirpath, f)).relative_to(self.project_root))
                    files.append(rel)
                    if len(files) >= MAX_LIST_FILES:
                        return ToolResult(
                            status="truncated",
                            path=path,
                            files=files,
                            message=f"Results truncated at {MAX_LIST_FILES} entries",
                        )
        else:
            try:
                entries = sorted(os.listdir(target))
            except OSError as e:
                return ToolResult(
                    status="error",
                    path=path,
                    message=f"Cannot list directory: {e}",
                )

            for name in entries:
                full = target / name
                rel = str(full.relative_to(self.project_root))
                if full.is_dir():
                    files.append(f"{rel}/")
                else:
                    files.append(rel)

        return ToolResult(
            status="success",
            path=path,
            files=files,
        )

    def search_files(
        self, query: str, path: str = ".", max_results: int = MAX_SEARCH_RESULTS
    ) -> ToolResult:
        """Search for text in project files."""
        target = self._resolve(path)

        if not target.exists():
            return ToolResult(
                status="error",
                path=path,
                message=f"Search path not found: {path}",
            )

        matches: list[dict] = []
        query_lower = query.lower()

        search_dirs: list[Path] = []
        if target.is_dir():
            search_dirs.append(target)
        else:
            search_dirs.append(target.parent)

        for search_dir in search_dirs:
            for dirpath, dirnames, filenames in os.walk(search_dir):
                dirnames[:] = [d for d in dirnames if not match_ignored(d)]

                for filename in filenames:
                    if len(matches) >= max_results:
                        break

                    filepath = Path(dirpath) / filename

                    try:
                        rel = str(filepath.relative_to(self.project_root))
                    except ValueError:
                        continue

                    try:
                        text = filepath.read_text(encoding="utf-8")
                    except (UnicodeDecodeError, OSError):
                        continue

                    if len(text) > 500_000:
                        continue

                    for line_num, line in enumerate(text.splitlines(), 1):
                        if query_lower in line.lower():
                            matches.append({
                                "path": rel,
                                "line": line_num,
                                "text": line.strip()[:200],
                            })
                            if len(matches) >= max_results:
                                break

            if len(matches) >= max_results:
                break

        status = "truncated" if len(matches) >= max_results else "success"
        return ToolResult(
            status=status,
            query=query,
            matches=matches,
            path=path,
        )
