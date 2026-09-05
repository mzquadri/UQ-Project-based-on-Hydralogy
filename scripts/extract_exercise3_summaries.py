"""Lift the small Exercise 3 (ROPE) summary artifacts out of the archive.

The Exercise 3 material lives in code/EX3/rope_exercise3_pycodes_Final.zip, which
is 2.1 GB and tracked with Git LFS. Almost all of that weight is simulation output
and a checked-in virtual environment; the numbers that describe what the analysis
concluded are a handful of small text and CSV files.

Cloning 2.1 GB to read 20 KB is a poor trade, so this script copies just those
summary files into results/exercise3_rope/. Nothing is modified or removed inside
the archive, which remains the source of record.

    python scripts/extract_exercise3_summaries.py

Output: results/exercise3_rope/
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "code" / "EX3" / "rope_exercise3_pycodes_Final.zip"
OUT = ROOT / "results" / "exercise3_rope"

#: Only the files that state a result. Suffix match, so the long paths inside the
#: archive do not have to be spelled out.
WANTED = (
    "420_rope_selected_threshold.txt",
    "420_threshold_sweep_summary.csv",
    "420_prms_rope_bounds.csv",
    "420_prms_rope_bounds_FINAL.csv",
    "420_summary.txt",
)

#: The two calibration periods the exercise was run over.
PERIODS = ("hbv_daily_1971_1980_cb", "hbv_daily_1981_1990_cb")


def is_lfs_pointer(path: Path) -> bool:
    """An un-fetched LFS file is a short text stub, not a zip."""
    with path.open("rb") as handle:
        return handle.read(40).startswith(b"version https://git-lfs")


def main() -> int:
    if not ARCHIVE.is_file():
        print(f"{ARCHIVE.relative_to(ROOT).as_posix()} is missing.", file=sys.stderr)
        return 1
    if is_lfs_pointer(ARCHIVE):
        print(
            "The Exercise 3 archive is still an LFS pointer. Fetch it first:\n"
            "  git lfs install && git lfs pull",
            file=sys.stderr,
        )
        return 1

    written = 0
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        for period in PERIODS:
            for wanted in WANTED:
                # Take the shallowest match, which is the top-level result for the
                # period rather than one of the per-threshold sweep directories.
                hits = [
                    n for n in names
                    if f"/{period}/" in n and n.endswith(wanted)
                    and "/thr_" not in n.split(period, 1)[1]
                ]
                if not hits:
                    continue
                source = min(hits, key=lambda n: n.count("/"))
                target = OUT / period / wanted
                target.parent.mkdir(parents=True, exist_ok=True)
                # Normalise to LF so the files read the same on every platform and
                # the extraction is byte-identical wherever it is run. The archive
                # was built on Windows, so its members carry CRLF.
                text = archive.read(source).decode("utf-8", "replace")
                text = "\n".join(text.splitlines()) + "\n"
                target.write_text(text, encoding="utf-8", newline="\n")
                written += 1
                print(f"  {period}/{wanted}")

    if not written:
        print("No Exercise 3 summary files matched.", file=sys.stderr)
        return 1
    print(f"\n{written} files written to {OUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
