from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import csv
import json
import re
import time


DATASET_DIR = Path(__file__).parent / "dataset"
MANIFEST_PATH = Path(__file__).parent / "dataset_manifest.csv"

TARGET_FILES = 30
DELAY_SECONDS = 2.0

API_URL = "https://gutendex.com/books"


def safe_filename(text, max_length=80):
    text = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        text = "book"
    return text[:max_length]


def get_books(target):
    books = []
    page_url = API_URL + "?" + urlencode({
        "languages": "en",
        "copyright": "false",
        "mime_type": "text/plain",
        "sort": "popular",
    })

    while page_url and len(books) < target:
        print(f"Mengambil metadata: {page_url}")

        req = Request(
            page_url,
            headers={"User-Agent": "B3-GlobalWordCount-StudentProject/1.0"}
        )

        with urlopen(req, timeout=30) as response:
            data = json.load(response)

        for book in data.get("results", []):
            formats = book.get("formats", {})

            text_url = None

            # Prioritaskan UTF-8 plain text.
            for key, value in formats.items():
                if key.startswith("text/plain") and "utf-8" in key.lower():
                    text_url = value
                    break

            # Fallback ke format text/plain apa pun.
            if text_url is None:
                for key, value in formats.items():
                    if key.startswith("text/plain"):
                        text_url = value
                        break

            if text_url:
                books.append({
                    "id": book.get("id"),
                    "title": book.get("title", "Unknown"),
                    "authors": "; ".join(
                        author.get("name", "")
                        for author in book.get("authors", [])
                    ),
                    "url": text_url,
                })

            if len(books) >= target:
                break

        page_url = data.get("next")

    return books[:target]


def download_file(url, destination):
    req = Request(
        url,
        headers={
            "User-Agent": "B3-GlobalWordCount-StudentProject/1.0"
        }
    )

    with urlopen(req, timeout=60) as response:
        content = response.read()

    destination.write_bytes(content)


def main():
    DATASET_DIR.mkdir(exist_ok=True)

    print("=" * 70)
    print("B3 - DOWNLOAD DATASET TEKS NYATA")
    print("=" * 70)
    print(f"Target file : {TARGET_FILES}")
    print(f"Folder      : {DATASET_DIR}")
    print()

    books = get_books(TARGET_FILES)

    if len(books) < TARGET_FILES:
        raise RuntimeError(
            f"Hanya ditemukan {len(books)} buku dengan plain-text. "
            f"Diperlukan minimal {TARGET_FILES}."
        )

    manifest_rows = []

    for index, book in enumerate(books, start=1):
        title = safe_filename(book["title"])
        filename = f"{index:02d}_pg{book['id']}_{title}.txt"
        destination = DATASET_DIR / filename

        print(f"[{index:02d}/{TARGET_FILES}] {book['title']}")

        if destination.exists() and destination.stat().st_size > 0:
            print("  -> sudah ada, dilewati")
        else:
            try:
                download_file(book["url"], destination)
                print(
                    f"  -> selesai ({destination.stat().st_size / 1024:.1f} KB)"
                )
                time.sleep(DELAY_SECONDS)
            except Exception as exc:
                print(f"  -> GAGAL: {exc}")
                continue

        manifest_rows.append({
            "index": index,
            "gutenberg_id": book["id"],
            "title": book["title"],
            "authors": book["authors"],
            "filename": filename,
            "source_url": book["url"],
        })

    # Simpan manifest agar sumber dataset dapat ditunjukkan di laporan.
    with MANIFEST_PATH.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "index",
                "gutenberg_id",
                "title",
                "authors",
                "filename",
                "source_url",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    txt_files = sorted(DATASET_DIR.glob("*.txt"))

    print()
    print("=" * 70)
    print(f"File .txt berhasil tersedia : {len(txt_files)}")
    print(f"Manifest                     : {MANIFEST_PATH.name}")
    print("=" * 70)

    if len(txt_files) < TARGET_FILES:
        print(
            "PERINGATAN: file yang berhasil diunduh masih kurang dari 30."
        )
    else:
        print("Dataset B3 siap digunakan.")


if __name__ == "__main__":
    main()
