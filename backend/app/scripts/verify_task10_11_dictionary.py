"""Read-only, resumable exact-headword verification against Akademos (IRYa RAN).

The website's GET `query` parameter is used (not the unrelated `word` form
parameter). Network failures are kept distinct from absent dictionary entries.
The evidence file stores facts/headwords and response hashes, not definitions.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from app.scripts.curated_task10_11_practice import FIPI, GRAMOTA_SUFFIX, candidate_cards


def normalize_headword(value: str) -> str:
    return re.sub(r"[\u0300\u0301\u00ad\d¹²³⁴⁵]", "", value).strip().rstrip("*;,.: ").casefold()


def expand_titles(titles: list[str]) -> list[str]:
    result = set()
    for title in titles:
        title = normalize_headword(title)
        match = re.fullmatch(r"(.+)\((ся|сь)\)", title)
        result.update([match[1], match[1] + match[2]] if match else [title])
    return sorted(result)


def headwords(source: str) -> list[str]:
    matches = re.findall(r'<span\s+class="title(?:\s+marked)?"[^>]*>\s*<b>(.*?)</b>\s*</span>', source, re.S)
    return expand_titles([html.unescape(re.sub(r"<[^>]+>", "", item)) for item in matches])


def verify(word: str, cache: Path | None = None) -> tuple[str, dict]:
    url = "https://orfo.ruslang.ru/search/word?" + urllib.parse.urlencode({"query": word, "title_check": 1, "text_check": 0, "yo": 1})
    record = {"url": url, "checkedAt": datetime.now(timezone.utc).isoformat(), "provider": "IRYa RAN / Akademos"}
    for attempt in range(3):
        try:
            time.sleep(0.15)
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Pumrus spelling verification)"})
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read()
            source = raw.decode("utf-8")
            titles = sorted(set(headwords(source)))
            if not titles and "не найдено" not in source:
                raise ValueError("Unexpected dictionary response: no result titles or absence marker")
            digest = hashlib.sha256(raw).hexdigest()
            if cache:
                (cache / f"{digest}.html").write_bytes(raw)
            return word, {**record, "status": "verified" if normalize_headword(word) in titles else "not_found", "headwords": titles, "responseSha256": digest}
        except Exception as exc:
            if attempt == 2:
                return word, {**record, "status": "error", "error": f"{type(exc).__name__}: {exc}"}
            time.sleep(attempt + 1)
    raise AssertionError("unreachable")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--workers", type=int, choices=[1, 2, 3], default=2)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--fipi-pdf", type=Path, help="Optional downloaded official 2026 navigator: verify explicitly listed examples")
    parser.add_argument("--gramota-suffix-html", type=Path, help="Downloaded official Gramota suffix explanation for асфальтщик")
    args = parser.parse_args()
    if args.cache:
        args.cache.mkdir(parents=True, exist_ok=True)
    evidence = json.loads(args.evidence.read_text(encoding="utf-8")) if args.evidence.exists() else {}
    for word, record in evidence.items():
        if record.get("status") in {"verified", "not_found"} and record.get("verificationMethod") != "official_example":
            record["headwords"] = expand_titles(record.get("headwords", []))
            record["status"] = "verified" if normalize_headword(word) in record["headwords"] else "not_found"
    words = sorted({card["lexeme"] for card in candidate_cards()})
    pending = [word for word in words if args.refresh or evidence.get(word, {}).get("status") not in {"verified", "not_found"}]
    args.evidence.parent.mkdir(parents=True, exist_ok=True)

    def save():
        temporary = args.evidence.with_suffix(".tmp")
        temporary.write_text(json.dumps(dict(sorted(evidence.items())), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(args.evidence)

    print(f"Exact dictionary checks: {len(words)} words, {len(pending)} pending", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(verify, word, args.cache) for word in pending]
        for done, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            word, record = future.result()
            evidence[word] = record
            if done % 25 == 0:
                save()
                print(f"Checked {done}/{len(pending)}: {dict(Counter(r['status'] for r in evidence.values()))}", flush=True)
    if args.fipi_pdf:
        from pypdf import PdfReader
        pages = [page.extract_text().replace("\u0301", "").casefold() for page in PdfReader(args.fipi_pdf).pages]
        response_hash = hashlib.sha256(args.fipi_pdf.read_bytes()).hexdigest()
        for word in words:
            if evidence[word]["status"] == "verified":
                continue
            for index, page_text in enumerate(pages):
                if re.search(r"(?<![а-яё])" + re.escape(word) + r"(?![а-яё])", page_text):
                    evidence[word] = {"status": "verified", "provider": "FIPI official navigator 2026", "verificationMethod": "official_example", "headwords": [word], "url": f"{FIPI}#page={index + 1}", "responseSha256": response_hash, "checkedAt": datetime.now(timezone.utc).isoformat()}
                    break
    if args.gramota_suffix_html:
        raw = args.gramota_suffix_html.read_bytes()
        source = html.unescape(re.sub(r"<[^>]+>", " ", raw.decode("utf-8")))
        if "асфальтщик" not in source or "суффикс" not in source:
            raise ValueError("The Gramota source does not contain the required suffix example")
        evidence["асфальтщик"] = {"status": "verified", "provider": "Gramota official spelling reference", "verificationMethod": "official_rule_example", "headwords": ["асфальтщик"], "url": GRAMOTA_SUFFIX, "responseSha256": hashlib.sha256(raw).hexdigest(), "checkedAt": datetime.now(timezone.utc).isoformat()}
    save()
    print(json.dumps(dict(Counter(evidence[word]["status"] for word in words)), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
