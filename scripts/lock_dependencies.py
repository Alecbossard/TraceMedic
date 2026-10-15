"""Record the actually tested dependency closure without an editable local path."""

from importlib.metadata import distributions
from pathlib import Path

rows = []
for distribution in distributions():
    name = distribution.metadata["Name"]
    if name.lower() in ("pip", "setuptools", "tracemedic"):
        continue
    row = f"{name}=={distribution.version}"
    if name.lower() == "pywin32":
        row += '; sys_platform == "win32"'
    rows.append(row)
Path("requirements.lock").write_text(
    "# Tested dependency closure on Python 3.13; pywin32 is Windows-only.\n"
    + "\n".join(sorted(set(rows), key=str.lower))
    + "\n"
)
