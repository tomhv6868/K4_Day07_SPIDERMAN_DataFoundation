"""Validate metadata and sources.csv for the K4 ecommerce documents."""

import csv
import re
from pathlib import Path

DATA_DIR = Path("data/k4_ecommerce")
REQUIRED = ["doc_id", "title", "source_url", "retrieved_at", "document_version"]
ROLE_KEY = "customer_role"


def frontmatter(document):
    parts = document.read_text(encoding="utf-8").split("---", 2)
    if len(parts) < 3:
        return {}
    return dict(re.findall(r"^(\w+):\s*(.+)$", parts[1], re.M))


def main():
    documents = sorted(DATA_DIR.glob("*.md"))
    with (DATA_DIR / "sources.csv").open(encoding="utf-8-sig", newline="") as file:
        source_rows = list(csv.DictReader(file))

    ids = []
    roles = {}
    for document in documents:
        metadata = frontmatter(document)
        doc_id = metadata.get("doc_id")
        ids.append(doc_id)
        role = metadata.get(ROLE_KEY)
        roles[role] = roles.get(role, 0) + 1
        valid = (
            all(field in metadata for field in REQUIRED)
            and ROLE_KEY in metadata
            and doc_id == document.stem
        )
        print("{:<40} {}".format(document.name, "OK" if valid else "THIEU METADATA"))

    csv_ids = sorted(row["doc_id"] for row in source_rows)
    print("so file :", len(documents), "(can 5-10)")
    print("csv     :", "khop" if csv_ids == sorted(ids) else "LECH")
    print(ROLE_KEY, ":", roles)


if __name__ == "__main__":
    main()
