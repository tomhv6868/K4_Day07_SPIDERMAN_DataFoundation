#!/usr/bin/env python3
"""Làm sạch corpus K4 sau khi chạy fetch_public_pages.py.

`fetch_public_pages.py` giữ lại menu, breadcrumb, khối "tin liên quan" và footer
của trang gốc. Script này fetch lại HTML, trích đúng khối nội dung chính theo
từng nguồn, chuyển sang Markdown và ghi đè file trong data/k4_ecommerce/.

Front matter được ghi KHÔNG dùng dấu nháy để khớp với script kiểm tra ở
docs/DATA_COLLECTION.md mục 6 (script đó so sánh doc_id thô với tên file).

    python3 scripts/clean_k4_corpus.py data/urls.csv --output-dir data/k4_ecommerce
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

USER_AGENT = "Day7DataFoundationsCourse/1.0 (+educational-lab)"
MANIFEST_FIELDS = [
    "doc_id", "file_path", "title", "source_url",
    "retrieved_at", "document_version", "license_or_permission",
]

# Khối nội dung chính của từng nguồn: (tên thẻ, regex khớp thuộc tính class/id).
CONTENT_CONTAINERS: dict[str, list[tuple[str, str]]] = {
    # Học viện Tiki dựng bài bằng Elementor: đoạn mở đầu nằm trong text-editor,
    # phần hỏi–đáp nằm trong widget toggle (giữ nguyên khối để tiêu đề đi kèm nội dung).
    "hocvien.tiki.vn": [("div", r"elementor-text-editor"), ("div", r"elementor-widget-toggle")],
    "www.bvntd.gov.vn": [("div", r"elementor-text-editor")],
    "dnvntd.bvntd.gov.vn": [("section", r"format-text"), ("div", r"content-dieu-le")],
    "moit.gov.vn": [("div", r"article-brief"), ("div", r"article-content[^\"]*common-content")],
}

# Dòng rác còn sót lại sau khi trích container.
NOISE_LINES = [
    r"^Nội dung này có hữu ích", r"^Gửi đánh giá", r"^Đánh giá trung bình",
    r"^Nếu bạn thấy nội dung này hữu ích", r"^Hãy chia sẻ ngay", r"^Ôi\b",
    r"^Bạn có thể cho Tiki biết", r"^Gửi phản hồi", r"^Copy link", r"^Xem thêm >$",
    r"^Các tin khác$", r"^Tin liên quan$", r"^Trang chủ$", r"^Skip to content$",
    r"^Chia sẻ", r"^Chương trình Freeship Xtra", r"^Tiki$", r"^Trung Tâm Bán Hàng$",
    r"^YouTube Tiki University Official$", r"^Cộng Đồng Nhà Bán Hàng Tiki$",
    r"^Hotline: ", r"^hotro@tiki\.vn$", r"^Địa chỉ văn phòng:", r"^Giấy chứng nhận",
    r"^©\s*\d{4}", r"^[-–|●\s]*$",
]
NOISE_RE = re.compile("|".join(NOISE_LINES))
BLOCK_TAGS = {"p", "br", "li", "tr", "div", "section", "h1", "h2", "h3", "h4", "h5", "h6"}


def flatten_tables(fragment: str) -> str:
    """Ép mỗi <table> thành các dòng `ô | ô` để không mất cặp giá trị của bảng."""

    def render(match: re.Match[str]) -> str:
        rows = []
        for row in re.findall(r"(?is)<tr\b[^>]*>(.*?)</tr>", match.group(0)):
            cells = re.findall(r"(?is)<t[dh]\b[^>]*>(.*?)</t[dh]>", row)
            cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", cell))).strip() for cell in cells]
            if any(cells):
                rows.append(" | ".join(cells))
        return "\n" + "\n".join(rows) + "\n"

    return re.sub(r"(?is)<table\b.*?</table>", render, fragment)


def strip_tags(fragment: str) -> str:
    """Chuyển một đoạn HTML thành text, giữ ranh giới đoạn/heading/list/bảng."""
    fragment = re.sub(r"(?is)<(script|style|noscript|svg|iframe)\b.*?</\1>", " ", fragment)
    fragment = re.sub(r"(?s)<!--.*?-->", " ", fragment)
    fragment = flatten_tables(fragment)
    fragment = re.sub(r"(?i)<(h[1-6])\b[^>]*>", r"\n\n## ", fragment)
    fragment = re.sub(r"(?i)</h[1-6]>", "\n\n", fragment)
    fragment = re.sub(r"(?i)<li\b[^>]*>", "\n- ", fragment)
    for tag in BLOCK_TAGS:
        fragment = re.sub(rf"(?i)</?{tag}\b[^>]*>", "\n", fragment)
    fragment = re.sub(r"(?s)<[^>]+>", " ", fragment)
    fragment = html.unescape(fragment)
    fragment = fragment.replace(" ", " ").replace("​", "")
    fragment = re.sub(r"[ \t]+", " ", fragment)
    return fragment


def extract_container(body: str, tag: str, class_pattern: str) -> list[tuple[int, str]]:
    """Trả về `(vị_trí, nội_dung)` của các thẻ `tag` có class khớp (khớp thẻ cân bằng)."""
    opener = re.compile(rf"<{tag}\b[^>]*(?:class|id)=\"[^\"]*(?:{class_pattern})[^\"]*\"[^>]*>", re.I)
    any_tag = re.compile(rf"</?{tag}\b[^>]*>", re.I)
    blocks: list[tuple[int, str]] = []
    for match in opener.finditer(body):
        depth, cursor = 1, match.end()
        while depth and (nxt := any_tag.search(body, cursor)):
            depth += -1 if nxt.group(0).startswith("</") else 1
            cursor = nxt.end()
        blocks.append((match.start(), body[match.end(): cursor]))
    return blocks


def to_markdown(body: str, host: str) -> str:
    rules = CONTENT_CONTAINERS.get(host)
    if not rules:
        raise ValueError(f"chưa khai báo khối nội dung cho host: {host}")

    # Gộp mọi khối rồi sắp theo vị trí trong HTML để giữ đúng thứ tự đọc của bài viết.
    blocks = sorted(block for tag, pattern in rules for block in extract_container(body, tag, pattern))

    seen: set[str] = set()
    lines: list[str] = []
    covered = 0  # bỏ qua khối lồng bên trong khối đã lấy, tránh lặp nội dung
    for start, block in blocks:
        if start < covered:
            continue
        covered = start + len(block)
        for raw in strip_tags(block).splitlines():
            line = raw.strip()
            if not line or NOISE_RE.match(line):
                continue
            # Chỉ khử trùng lặp các dòng ngắn (nhãn menu, tiêu đề widget lặp lại);
            # câu nội dung dài trùng nhau vẫn giữ vì có thể thuộc hai mục khác nhau.
            if len(line) < 80:
                if line in seen:
                    continue
                seen.add(line)
            lines.append(line)

    text = "\n\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def published_date(body: str) -> str:
    """Ngày đăng từ thẻ meta, dùng làm document_version khi nguồn không nêu phiên bản."""
    for pattern in (
        r'property="article:published_time"[^>]*content="(\d{4}-\d{2}-\d{2})',
        r'itemprop="datePublished"[^>]*content="(\d{4}-\d{2}-\d{2})',
        r'content="(\d{4}-\d{2}-\d{2})[^"]*"[^>]*itemprop="datePublished"',
    ):
        if found := re.search(pattern, body, re.I):
            return found.group(1)
    return ""


def yaml_block(metadata: dict[str, str]) -> str:
    return "\n".join(f"{key}: {value}" for key, value in metadata.items())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--min-chars", type=int, default=600)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.input_csv.open(encoding="utf-8")))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, str]] = {}
    failures = 0

    for index, row in enumerate(rows):
        url = row["url"].strip()
        host = urlparse(url).netloc
        if index:
            time.sleep(args.delay)
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "vi"})
            with urlopen(request, timeout=30) as response:  # noqa: S310 - URL do người dùng cung cấp
                body = response.read().decode(response.headers.get_content_charset() or "utf-8", "replace")
                final_url = response.geturl()
            content = to_markdown(body, host)
            if len(content) < args.min_chars:
                raise ValueError(f"nội dung sau khi làm sạch quá ngắn ({len(content)} ký tự)")

            version = row.get("document_version", "").strip()
            if version in ("", "not-stated"):
                version = published_date(body) or "not-stated"

            metadata = {
                "doc_id": row["doc_id"].strip(),
                "title": row["title"].strip(),
                "source_url": final_url,
                "retrieved_at": date.today().isoformat(),
                "document_version": version,
                "customer_role": row["customer_role"].strip(),
                "category": row["category"].strip(),
                "language": row.get("language", "vi").strip(),
            }
            path = args.output_dir / f"{metadata['doc_id']}.md"
            path.write_text(
                f"---\n{yaml_block(metadata)}\n---\n\n# {metadata['title']}\n\n{content}\n",
                encoding="utf-8",
            )
            manifest[metadata["doc_id"]] = {
                "doc_id": metadata["doc_id"],
                "file_path": str(path),
                "title": metadata["title"],
                "source_url": metadata["source_url"],
                "retrieved_at": metadata["retrieved_at"],
                "document_version": metadata["document_version"],
                "license_or_permission": row.get("license_or_permission") or "public-page",
            }
            print(f"Đã làm sạch {path} ({len(content)} ký tự, version={version})")
        except Exception as error:  # noqa: BLE001 - báo lỗi rồi chuyển sang URL kế tiếp
            failures += 1
            print(f"Bỏ qua {url}: {error}", file=sys.stderr)

    manifest_path = args.output_dir / "sources.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for doc_id in sorted(manifest):
            writer.writerow(manifest[doc_id])
    print(f"Xong: {len(manifest)} tài liệu, {failures} lỗi. Manifest: {manifest_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
