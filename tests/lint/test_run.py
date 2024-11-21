# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/pylint-dev/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/pylint-dev/pylint/blob/main/CONTRIBUTORS.txt

from pathlib import Path

import pytest
from unittest.mock import MagicMock, mock_open, patch

from typing import Any, Protocol
from io import BufferedReader

from pylint import lint
from pylint.testutils.utils import _test_cwd


@pytest.mark.parametrize(
    "contents,expected",
    [
        ("50000 100000", 1),
        ("100000 100000", 1),
        ("200000 100000", 2),
        ("299999 100000", 2),
        ("300000 100000", 3),
        # Unconstrained cgroup
        ("max 100000", None),
    ],
)
def test_query_cpu_cgroupv2(
        tmp_path: Path,
        contents: str,
        expected: int,
) -> None:
    """Check that `pylint.lint.run._query_cpu` generates realistic values in cgroupsv2 systems.
    """
    builtin_open = open

    def _mock_open(*args: Any, **kwargs: Any) -> BufferedReader:
        if args[0] == "/sys/fs/cgroup/cpu.max":
            return mock_open(read_data=contents)(*args, **kwargs)  # type: ignore[no-any-return]
        return builtin_open(*args, **kwargs)  # type: ignore[no-any-return]

    pathlib_path = Path

    def _mock_path(*args: str, **kwargs: Any) -> Path:
        if args[0] == "/sys/fs/cgroup/cpu/cpu.shares":
            return MagicMock(is_file=lambda: False)
        if args[0] == "/sys/fs/cgroup/cpu/cfs_quota_us":
            return MagicMock(is_file=lambda: False)
        if args[0] == "/sys/fs/cgroup/cpu.max":
            return MagicMock(is_file=lambda: True)
        return pathlib_path(*args, **kwargs)

    with _test_cwd(tmp_path):
        with patch("builtins.open", _mock_open):
            with patch("pylint.lint.run.Path", _mock_path):
                cpus = lint.run._query_cpu()
                assert cpus == expected
