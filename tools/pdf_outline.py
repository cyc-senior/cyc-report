"""Measure an example report PDF so its layout and outline can be copied into LaTeX.

Usage:
    pip install pymupdf
    python tools/pdf_outline.py <example.pdf> [--pages N]

Prints:
  1. page size and page count
  2. the bookmark outline (chapters/sections/subsections with page numbers)
  3. the first line of each of the first pages (front matter order)
  4. font sizes: body size, heading sizes with a sample of their text
  5. text margins in cm, and where the page number sits
  6. sample caption lines (รูปที่ / ตารางที่ / Figure / Table)

Text extraction of Thai can come out garbled for some fonts; the bookmark
outline (2) is reliable even then. See AGENTS.md for how to use the output.
"""
import argparse
import collections
import re
import sys

try:
    import pymupdf
except ImportError:  # older PyMuPDF
    import fitz as pymupdf

PT_PER_CM = 72 / 2.54


def cm(v):
    return f"{v / PT_PER_CM:.2f}cm"


def spans(page):
    for b in page.get_text("dict")["blocks"]:
        for line in b.get("lines", []):
            for s in line["spans"]:
                t = s["text"].strip()
                if t:
                    yield s, t, line["bbox"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", type=int, default=14, help="front-matter pages to list (default 14)")
    a = ap.parse_args()
    doc = pymupdf.open(a.pdf)
    w, h = doc[0].rect.width, doc[0].rect.height

    print(f"== 1. Pages: {doc.page_count}, size {cm(w)} x {cm(h)}")

    print("\n== 2. Outline (level, title, page)")
    toc = doc.get_toc()
    if not toc:
        print("  (no bookmarks)")
    for lvl, title, pg in toc:
        print(f"  {'  ' * (lvl - 1)}[{lvl}] {title}  ....  p{pg}")

    print(f"\n== 3. First line of the first {a.pages} pages")
    for i in range(min(a.pages, doc.page_count)):
        first = next((t for _, t, _ in spans(doc[i])), "(empty)")
        print(f"  p{i + 1}: {first[:90]}")

    # Font statistics over all pages
    by_size = collections.Counter()
    samples = collections.defaultdict(list)
    x0s, x1s, y0s, y1s, numbers = [], [], [], [], []
    for i, page in enumerate(doc):
        page_spans = list(spans(page))
        for s, t, bbox in page_spans:
            key = (round(s["size"], 1), "bold" if s["flags"] & 16 or "Bold" in s["font"] else "regular")
            by_size[key] += len(t)
            if len(samples[key]) < 4 and len(t) > 2:
                samples[key].append(f"p{i + 1}: {t[:60]}")
        if i >= 8 and page_spans:  # skip covers/front matter for margins
            for s, t, bbox in page_spans:
                if re.fullmatch(r"[0-9ivxlc]+", t) and bbox[1] > h * 0.85:
                    numbers.append(((bbox[0] + bbox[2]) / 2, h - bbox[3]))
                    continue
                x0s.append(bbox[0]); x1s.append(bbox[2]); y0s.append(bbox[1]); y1s.append(bbox[3])

    print("\n== 4. Font sizes (pt, weight): characters, samples")
    body = by_size.most_common(1)[0][0] if by_size else None
    for key, n in sorted(by_size.items(), key=lambda kv: -kv[0][0]):
        if n < 20:
            continue
        tag = "  <- body" if key == body else ""
        print(f"  {key[0]:>5}pt {key[1]:<7} {n:>7} chars{tag}")
        for smp in samples[key]:
            print(f"        {smp}")

    if x0s:
        q = lambda xs, p: sorted(xs)[int(len(xs) * p)]
        print("\n== 5. Text margins (5th/95th percentile, body pages)")
        print(f"  left {cm(q(x0s, 0.05))}  right {cm(w - q(x1s, 0.95))}  "
              f"top {cm(q(y0s, 0.05))}  bottom {cm(h - q(y1s, 0.95))}")
    if numbers:
        xs = sorted(n[0] for n in numbers); ys = sorted(n[1] for n in numbers)
        pos = "centre" if abs(xs[len(xs) // 2] - w / 2) < w * 0.08 else ("right" if xs[len(xs) // 2] > w / 2 else "left")
        print(f"  page number: bottom {pos}, baseline ~{cm(ys[len(ys) // 2])} from the bottom edge")

    print("\n== 6. Caption samples")
    shown = 0
    for i, page in enumerate(doc):
        for _, t, _ in spans(page):
            if re.match(r"(รูปที่|ตารางที่|Figure|Table)\s*\d", t) and shown < 8:
                print(f"  p{i + 1}: {t[:90]}")
                shown += 1
    if not shown:
        print("  (none found; captions may be split across spans)")


if __name__ == "__main__":
    sys.exit(main())
