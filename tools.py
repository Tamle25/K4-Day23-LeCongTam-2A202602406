"""tools.py - STUDENT IMPLEMENTS.  Source tools for the research agents.   Guide: GUIDE.md, part 1.

Rules for every tool:
  * runs on the HOST (not in the sandbox): API keys must never enter the sandbox;
  * returns a STRING (JSON text of compact records) and NEVER raises:
        "NO RESULTS"  when the source answers with nothing,
        "ERROR: ..."  when the source keeps failing after the retries (the agent then tries another source);
  * the docstring is the tool description the LLM reads: keep it precise (what it does, what it returns, when to use it).
Try your tools without any agent:   python tools.py
"""
import json
import os
import random
import re
import time
import xml.etree.ElementTree

import httpx
from langchain_core.tools import tool

# ---- constants (given) ----
ARXIV_URL = "https://export.arxiv.org/api/query"  # https only: http answers 301
HF_DAILY_URL = "https://huggingface.co/api/daily_papers"
HF_SEARCH_URL = "https://huggingface.co/api/papers/search"
EXA_URL = "https://mcp.exa.ai/mcp"


class RetryableError(Exception):
    """Given. Raise it inside a call to ask with_retry to wait and try again (retry_after in seconds, optional)."""

    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


# ---- TODO 1: retry helper ----
def with_retry(fn, *, attempts=5, base=1.0, cap=30.0):
    """Call fn(); when it raises RetryableError, wait and call it again.

    Treat these as retryable: RetryableError, HTTP 429/500/502/503/504,
    httpx.TransportError (timeouts, connection resets).
    Respect Retry-After header. Exponential backoff with jitter, capped at `cap`.
    Give up after `attempts` (do not sleep after the last attempt).
    """
    for attempt in range(attempts):
        try:
            return fn()
        except (RetryableError, httpx.TransportError, httpx.HTTPStatusError) as e:
            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code not in (429, 500, 502, 503, 504):
                raise

            if attempt == attempts - 1:
                raise

            retry_after = getattr(e, "retry_after", None)
            if retry_after is None and isinstance(e, httpx.HTTPStatusError):
                header = e.response.headers.get("retry-after")
                if header:
                    try:
                        retry_after = float(header)
                    except ValueError:
                        retry_after = None

            if retry_after is not None:
                delay = float(retry_after)
            else:
                delay = base * (2**attempt) + random.uniform(0.0, 1.0)

            delay = min(cap, delay)
            time.sleep(delay)


# ---- TODO 2: arXiv ----
_last_arxiv_time = 0.0


@tool
def arxiv_search(query: str, max_results: int = 10) -> str:
    """Search arXiv papers by keywords, newest first. Returns a JSON list of {id, url, published, title, summary}."""
    global _last_arxiv_time
    try:
        # Keep only word characters (alphanumeric and hyphens), discard empty or query punctuation
        terms = [t for t in re.findall(r"[\w-]+", query) if t.lower() not in {"and", "or", "not"}]
        if not terms:
            return "NO RESULTS"

        search_terms = " AND ".join(f"all:{t}" for t in terms)
        limit = max(1, min(max_results, 30))
        params = {
            "search_query": search_terms,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": limit,
        }

        def _call():
            global _last_arxiv_time
            # arXiv etiquette: at least 3 seconds between two arXiv calls
            elapsed = time.monotonic() - _last_arxiv_time
            if elapsed < 3.0:
                time.sleep(3.0 - elapsed)
            _last_arxiv_time = time.monotonic()

            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                resp = client.get(ARXIV_URL, params=params)
                if resp.status_code in (429, 500, 502, 503, 504):
                    retry_after = None
                    ra = resp.headers.get("retry-after")
                    if ra:
                        try:
                            retry_after = float(ra)
                        except ValueError:
                            pass
                    raise RetryableError(f"arXiv HTTP {resp.status_code}", retry_after=retry_after)
                resp.raise_for_status()
                return resp.text

        xml_text = with_retry(_call, attempts=5, base=2.0, cap=60.0)

        root = xml.etree.ElementTree.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        records = []
        for entry in root.findall("atom:entry", ns):
            id_elem = entry.find("atom:id", ns)
            if id_elem is None or not id_elem.text:
                continue
            raw_id = id_elem.text.strip().split("/abs/")[-1]
            # Strip version suffix (e.g., 2501.00001v1 -> 2501.00001)
            arxiv_id = re.sub(r"v\d+$", "", raw_id)
            url = f"https://arxiv.org/abs/{arxiv_id}"

            pub_elem = entry.find("atom:published", ns)
            published = pub_elem.text.strip()[:10] if pub_elem is not None and pub_elem.text else ""

            title_elem = entry.find("atom:title", ns)
            title = " ".join(title_elem.text.split()) if title_elem is not None and title_elem.text else ""

            sum_elem = entry.find("atom:summary", ns)
            summary = " ".join(sum_elem.text.split())[:600] if sum_elem is not None and sum_elem.text else ""

            records.append({
                "id": arxiv_id,
                "url": url,
                "published": published,
                "title": title,
                "summary": summary,
            })

        if not records:
            return "NO RESULTS"
        return json.dumps(records, ensure_ascii=False)
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"


# ---- TODO 3: Hugging Face ----
@tool
def hf_daily_papers(limit: int = 30, date: str = "", keyword: str = "") -> str:
    """Hugging Face Daily Papers = what is trending in AI research. Returns a JSON list of
    {id, url, published, title, summary, upvotes, github, stars} sorted by upvotes. `date` is YYYY-MM-DD (empty = latest).
    `keyword` filters title/summary; there is no topic search on this endpoint (use hf_search_papers for a topic)."""
    try:
        limit_clamped = max(1, min(limit, 100))
        params = {"limit": limit_clamped}
        if date:
            params["date"] = date

        def _call():
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                resp = client.get(HF_DAILY_URL, params=params)
                if resp.status_code in (429, 500, 502, 503, 504):
                    retry_after = None
                    ra = resp.headers.get("retry-after")
                    if ra:
                        try:
                            retry_after = float(ra)
                        except ValueError:
                            pass
                    raise RetryableError(f"HF Daily HTTP {resp.status_code}", retry_after=retry_after)
                resp.raise_for_status()
                return resp.json()

        items = with_retry(_call, attempts=5, base=1.0, cap=30.0)
        if not isinstance(items, list):
            return "NO RESULTS"

        records = []
        kw = keyword.lower().strip() if keyword else ""
        for item in items:
            paper = item.get("paper", {}) if isinstance(item, dict) else {}
            paper_id = paper.get("id")
            if not paper_id:
                continue

            title = " ".join(str(paper.get("title") or item.get("title") or "").split())
            summary = " ".join(str(paper.get("summary") or item.get("summary") or "").split())[:600]
            published = str(paper.get("publishedAt") or item.get("publishedAt") or "")[:10]
            upvotes = int(paper.get("upvotes") or 0)
            github = str(paper.get("githubRepo") or "")
            stars = int(paper.get("githubStars") or 0)

            if kw and (kw not in title.lower() and kw not in summary.lower()):
                continue

            records.append({
                "id": str(paper_id),
                "url": f"https://huggingface.co/papers/{paper_id}",
                "published": published,
                "title": title,
                "summary": summary,
                "upvotes": upvotes,
                "github": github,
                "stars": stars,
            })

        records.sort(key=lambda r: r.get("upvotes", 0), reverse=True)
        if not records:
            return "NO RESULTS"
        return json.dumps(records, ensure_ascii=False)
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"


@tool
def hf_search_papers(query: str, limit: int = 10) -> str:
    """Search Hugging Face papers by topic. Returns a JSON list of
    {id, url, published, title, summary, upvotes, github, stars}."""
    try:
        if not query.strip():
            return "NO RESULTS"
        limit_clamped = max(1, min(limit, 50))
        params = {"q": query.strip(), "limit": limit_clamped}

        def _call():
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                resp = client.get(HF_SEARCH_URL, params=params)
                if resp.status_code in (429, 500, 502, 503, 504):
                    retry_after = None
                    ra = resp.headers.get("retry-after")
                    if ra:
                        try:
                            retry_after = float(ra)
                        except ValueError:
                            pass
                    raise RetryableError(f"HF Search HTTP {resp.status_code}", retry_after=retry_after)
                resp.raise_for_status()
                return resp.json()

        items = with_retry(_call, attempts=5, base=1.0, cap=30.0)
        if not isinstance(items, list):
            return "NO RESULTS"

        records = []
        for item in items:
            paper = item.get("paper") if isinstance(item, dict) and "paper" in item else item
            if not isinstance(paper, dict):
                continue
            paper_id = paper.get("id")
            if not paper_id:
                continue

            title = " ".join(str(paper.get("title") or item.get("title") or "").split())
            raw_summary = paper.get("ai_summary") or paper.get("summary") or item.get("summary") or ""
            summary = " ".join(str(raw_summary).split())[:600]
            published = str(paper.get("publishedAt") or item.get("publishedAt") or "")[:10]
            upvotes = int(paper.get("upvotes") or 0)
            github = str(paper.get("githubRepo") or "")
            stars = int(paper.get("githubStars") or 0)

            records.append({
                "id": str(paper_id),
                "url": f"https://huggingface.co/papers/{paper_id}",
                "published": published,
                "title": title,
                "summary": summary,
                "upvotes": upvotes,
                "github": github,
                "stars": stars,
            })

        if not records:
            return "NO RESULTS"
        return json.dumps(records, ensure_ascii=False)
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"


# ---- TODO 4: web search / fetch through the Exa MCP endpoint ----
def _call_exa_mcp(tool_name: str, arguments: dict) -> str:
    """Call Exa MCP tools over plain HTTP JSON-RPC with rate limit handling and key masking."""
    api_key = os.environ.get("EXA_API_KEY", "").strip()
    url = f"{EXA_URL}?exaApiKey={api_key}" if api_key else EXA_URL
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }

    def _call():
        with httpx.Client(timeout=45.0, follow_redirects=True) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 429:
                retry_after = None
                ra = resp.headers.get("retry-after")
                if ra:
                    try:
                        retry_after = float(ra)
                    except ValueError:
                        pass
                raise RetryableError("Exa rate limited (HTTP 429)", retry_after=retry_after or 20.0)
            if resp.status_code in (500, 502, 503, 504):
                raise RetryableError(f"Exa HTTP {resp.status_code}")
            resp.raise_for_status()

            resp_text = resp.text
            parsed_data = None
            for line in resp_text.splitlines():
                if line.startswith("data:"):
                    line_content = line[5:].strip()
                    if line_content:
                        try:
                            parsed_data = json.loads(line_content)
                            break
                        except json.JSONDecodeError:
                            pass
            if parsed_data is None:
                try:
                    parsed_data = resp.json()
                except Exception:
                    parsed_data = {}

            # Check JSON-RPC error
            if "error" in parsed_data:
                err_msg = str(parsed_data["error"].get("message", ""))
                if "rate limit" in err_msg.lower():
                    raise RetryableError(f"Exa rate limit: {err_msg}", retry_after=20.0)
                raise RuntimeError(f"Exa error: {err_msg}")

            result = parsed_data.get("result", {})
            # Check rate limit flag in result._meta
            meta_str = json.dumps(result.get("_meta", {})).lower()
            if "rate" in meta_str and "limit" in meta_str:
                raise RetryableError("Exa rate limited (_meta)", retry_after=20.0)

            # Check content for free tier rate limit notices
            contents = result.get("content", [])
            texts = []
            for c in contents:
                if isinstance(c, dict) and c.get("type") == "text":
                    t = c.get("text", "")
                    if "rate limit" in t.lower() and "free mcp" in t.lower():
                        raise RetryableError("Exa rate limited (free tier message)", retry_after=20.0)
                    texts.append(t)
            return "\n\n".join(texts)

    try:
        raw_result = with_retry(_call, attempts=5, base=2.0, cap=60.0)
        return raw_result.strip() if raw_result.strip() else "NO RESULTS"
    except Exception as exc:
        err_str = f"ERROR: {type(exc).__name__}: {exc}"
        if api_key and api_key in err_str:
            err_str = err_str.replace(api_key, "[REDACTED]")
        return err_str


@tool
def web_search(query: str, objective: str = "", num_results: int = 5) -> str:
    """Search the web (Exa). Describe the ideal page in natural language. Returns clean text of the top results with URLs."""
    if not query.strip():
        return "NO RESULTS"
    obj = objective.strip() if objective.strip() else f"Find relevant information and survey papers on {query}"
    args = {
        "query": query.strip(),
        "objective": obj,
        "numResults": max(1, min(num_results, 10)),
    }
    return _call_exa_mcp("web_search_exa", args)


@tool
def web_fetch(url: str) -> str:
    """Read the full content of one web page (e.g. an arXiv abstract page) as markdown. Long pages are truncated."""
    if not url.strip():
        return "NO RESULTS"
    args = {"urls": [url.strip()]}
    res = _call_exa_mcp("web_fetch_exa", args)
    if res.startswith("ERROR:") or res == "NO RESULTS":
        return res
    return res[:12000]


# ---- TODO 5: registry (the researcher subagent gets exactly these) ----
SOURCE_TOOLS = [arxiv_search, hf_daily_papers, hf_search_papers, web_search, web_fetch]


if __name__ == "__main__":
    for name, fn, args in [
        ("arxiv_search", arxiv_search, {"query": "world model", "max_results": 3}),
        ("hf_daily_papers", hf_daily_papers, {"limit": 20}),
        ("hf_search_papers", hf_search_papers, {"query": "world model", "limit": 3}),
        ("web_search", web_search, {"query": "survey paper on world models", "num_results": 2}),
        ("web_fetch", web_fetch, {"url": "https://arxiv.org/abs/1803.10122"}),
    ]:
        try:
            print(f"== {name}\n{fn.invoke(args)[:400]}\n")
        except NotImplementedError as exc:
            print(f"== {name}: not implemented yet ({exc})\n")
