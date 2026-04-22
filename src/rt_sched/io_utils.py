from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


JsonDict = dict


def _iter_json_files(paths: Iterable[str], recursive: bool) -> Iterable[Path]:
    for p in paths:
        path = Path(p)

        if path.is_file() and path.suffix.lower() == ".json":
            yield path
            continue

        if path.is_dir():
            pattern = "**/*.json" if recursive else "*.json"
            yield from path.glob(pattern)


def load_datasets_from_paths(paths: Iterable[str], recursive: bool = True) -> list[JsonDict]:
    datasets: list[JsonDict] = []

    for json_file in _iter_json_files(paths, recursive=recursive):
        with json_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        if isinstance(data, dict) and "tasks" in data:
            data["_source_file"] = str(json_file)
            datasets.append(data)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "tasks" in item:
                    item["_source_file"] = str(json_file)
                    datasets.append(item)

    return datasets
