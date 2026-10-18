"""Download and extract the public MovieLens Latest Small dataset."""
from __future__ import annotations

import urllib.request
import zipfile
from pathlib import Path

URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ARCHIVE = DATA_DIR / "ml-latest-small.zip"
EXPECTED = DATA_DIR / "ml-latest-small" / "ratings.csv"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if EXPECTED.exists():
        print(f"Dataset already present: {EXPECTED.parent}")
        return
    print(f"Downloading {URL}")
    request = urllib.request.Request(URL, headers={"User-Agent": "PDS-MovieLens-MiniProject/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response, ARCHIVE.open("wb") as output:
        output.write(response.read())
    with zipfile.ZipFile(ARCHIVE) as archive:
        archive.extractall(DATA_DIR)
    if not EXPECTED.exists():
        raise RuntimeError("Archive extracted, but ratings.csv was not found at the expected path")
    print(f"Dataset ready at {EXPECTED.parent}")
    print("Record the download date and the dataset version stated in its README.txt for your report.")


if __name__ == "__main__":
    main()
