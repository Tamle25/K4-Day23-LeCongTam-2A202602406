"""check_citations.py - STUDENT IMPLEMENTS `check`.   Runs INSIDE the sandbox (standard library only).

research.py uploads this file to the sandbox and the lead agent runs it with the `execute` tool:
    python3 /tmp/work/research/check_citations.py [report.md] [sources.json]
It must exit 0 and print "OK: ..." when the report is consistent, else print each problem and exit 1.
"""
import json
import sys

REPORT = "/tmp/work/report/report.md"
SOURCES = "/tmp/work/research/sources.json"


import re

_GROUP = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\](?!\()")
_CODE = re.compile(r"(```.*?```|`[^`\n]*`)", re.DOTALL)
_REF_HEADING = re.compile(r"(?m)^##[ \t]+References[ \t]*$")


def _group_numbers(group_str):
    """Khai triển các dạng trích dẫn gộp như '1, 2' hoặc '1-3' thành danh sách số."""
    numbers = []
    for part in re.split(r"\s*,\s*", group_str):
        span = re.fullmatch(r"(\d+)\s*[–-]\s*(\d+)", part)
        if span:
            a, b = int(span.group(1)), int(span.group(2))
            if a <= b and b - a <= 200:
                numbers.extend(range(a, b + 1))
            else:
                numbers.extend([a, b])
        elif part.isdigit():
            numbers.append(int(part))
    return numbers


def check(report_text, sources):
    """Return a list of problem strings (empty list = OK)."""
    problems = []

    # 1. sources phải là danh sách không rỗng
    if not isinstance(sources, list) or len(sources) == 0:
        return ["no sources in sources.json"]

    # 2. Kiểm tra từng mục trong sources
    seen_urls = set()
    source_numbers = {}
    for entry in sources:
        if not isinstance(entry, dict):
            problems.append(f"invalid source entry (not a dict): {entry!r}")
            continue

        n = entry.get("n")
        if type(n) is not int:
            problems.append(f"source {entry!r}: 'n' must be an integer")
        elif n in source_numbers:
            problems.append(f"duplicate source number n={n} in sources.json")
        else:
            source_numbers[n] = entry

        url = entry.get("url")
        if not isinstance(url, str) or not (url.startswith("http://") or url.startswith("https://")):
            problems.append(f"source n={n!r}: invalid url {url!r}")
        elif url in seen_urls:
            problems.append(f"duplicate url in sources.json: {url}")
        else:
            seen_urls.add(url)

    # 3. Phải có tiêu đề ## References; tách phần thân và phần References
    ref_matches = list(_REF_HEADING.finditer(report_text))
    if not ref_matches:
        problems.append("missing '## References' heading in report")
        body = report_text
        ref_section = ""
    else:
        body = report_text[:ref_matches[-1].start()]
        ref_section = report_text[ref_matches[-1].end():]

    # 4. Tìm các [n] trong phần thân (bỏ qua khối mã và liên kết Markdown)
    segments = _CODE.split(body)
    cited = set()
    for i, segment in enumerate(segments):
        if i % 2 == 1:
            # Khối mã hoặc inline code: bỏ qua
            continue
        for match in _GROUP.finditer(segment):
            for n in _group_numbers(match.group(1)):
                cited.add(n)

    # Mọi [n] trong thân phải có trong sources
    for n in sorted(cited):
        if n not in source_numbers:
            problems.append(f"[{n}] cited in report body but missing from sources.json")

    # Mọi nguồn trong sources phải được trích dẫn ít nhất 1 lần
    for n in sorted(source_numbers.keys()):
        if n not in cited:
            problems.append(f"source [{n}] never cited in report body")

    # 5 & 6. Kiểm tra phần ## References
    ref_lines = []
    for line in ref_section.splitlines():
        line_s = line.strip()
        m = re.match(r"^\[(\d+)\]", line_s)
        if m:
            ref_lines.append((int(m.group(1)), line_s))

    ref_counts = {}
    for n, line_s in ref_lines:
        ref_counts[n] = ref_counts.get(n, 0) + 1

    # Kiểm tra số lần xuất hiện của mỗi [n] trong References
    for n, count in ref_counts.items():
        if count > 1:
            problems.append(f"reference [{n}] appears {count} times in References section")
        if n not in source_numbers:
            problems.append(f"reference [{n}] in References section is not in sources.json")

    for n in sorted(source_numbers.keys()):
        if n not in ref_counts:
            problems.append(f"missing reference line for source [{n}] in References section")

    # Kiểm tra URL trong mỗi dòng tham khảo
    for n, line_s in ref_lines:
        raw_urls = re.findall(r"https?://[^\s)\]]+", line_s)
        urls = [u.rstrip(".,;)") for u in raw_urls]
        if len(urls) == 0:
            problems.append(f"reference line [{n}] contains no URL: '{line_s}'")
        elif len(urls) > 1:
            problems.append(f"reference line [{n}] contains multiple URLs (bundling sources under one number is forbidden): '{line_s}'")
        else:
            ref_url = urls[0]
            if n in source_numbers:
                src_url = source_numbers[n].get("url")
                if ref_url != src_url:
                    problems.append(f"reference line [{n}] URL '{ref_url}' does not match sources.json URL '{src_url}'")

    return problems


def main(argv):
    report_path = argv[1] if len(argv) > 1 else REPORT
    sources_path = argv[2] if len(argv) > 2 else SOURCES
    try:
        with open(report_path, encoding="utf-8") as f:
            report = f.read()
        with open(sources_path, encoding="utf-8") as f:
            sources = json.load(f)
    except (OSError, ValueError) as exc:
        print(f"cannot read inputs: {exc}")
        return 1
    problems = check(report, sources)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"OK: {len(sources)} sources, all citations resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
