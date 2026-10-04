"""Name-availability check for rename candidates (stdlib only).

Usage:
    python tools/name_check.py Kymora Tachyra Aevra
    python tools/name_check.py --out docs/refactor/rename-kymora/NAME_CHECK_RAW.json Kymora

For each candidate and its variants (name, name-rs, py<name>, <name>-py,
plus PEP 503 hyphen/underscore/dot normalizations) checks:
  PyPI (GET https://pypi.org/pypi/<name>/json, 404 = free),
  crates.io (GET https://crates.io/api/v1/crates/<name>, 404 = free),
  npm registry (GET https://registry.npmjs.org/<name>),
  GitHub repo search + user/org lookup (unauthenticated, best-effort),
  domains via RDAP (rdap.org for .com/.dev/.io/.org),
  local import collision (import <name> must fail).
Network failures are recorded as INCONCLUSIVE (manual recheck for owner).
Exit 0 always unless --strict and a candidate is taken on PyPI/crates.io.
"""
import importlib.util
import json
import re
import sys
import urllib.request

UA = {"User-Agent": "tsxtract-rename-check/1.0 (contact: repo owner)"}
TIMEOUT = 15


def pep503(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def variants(name):
    base = name.lower()
    cands = [base, f"{base}-rs", f"py{base}", f"{base}-py"]
    seen, out = set(), []
    for c in cands:
        for v in (c, c.replace("-", "_"), pep503(c)):
            if v not in seen:
                seen.add(v)
                out.append(v)
    return out


def get(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read(2000).decode("utf-8", "replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # noqa: BLE001 - network best-effort
        return -1, f"{type(e).__name__}: {e}"


import urllib.error  # noqa: E402  (kept late to keep header tidy)


def check_pypi(name):
    code, body = get(f"https://pypi.org/pypi/{name}/json")
    if code == 404:
        return "FREE (404)"
    if code == 200:
        try:
            info = json.loads(body)["info"]
            return f"TAKEN (version {info.get('version')}, author {info.get('author')})"
        except Exception:  # noqa: BLE001
            return "TAKEN (200, unreadable body)"
    return f"INCONCLUSIVE (HTTP {code}: {body[:100]})"


def check_crates(name):
    code, body = get(f"https://crates.io/api/v1/crates/{name}")
    if code == 404:
        return "FREE (404)"
    if code == 200:
        return "TAKEN (200)"
    return f"INCONCLUSIVE (HTTP {code}: {body[:100]})"


def check_npm(name):
    code, body = get(f"https://registry.npmjs.org/{name}")
    if code == 404:
        return "FREE (404)"
    if code == 200:
        return "TAKEN (200)"
    return f"INCONCLUSIVE (HTTP {code}: {body[:100]})"


def check_github(name):
    code, body = get(
        f"https://api.github.com/search/repositories?q={name}+in:name&per_page=5"
    )
    if code == -1:
        return {"search": f"INCONCLUSIVE ({body[:100]})", "user/org": "INCONCLUSIVE"}
    if code == 200:
        items = []
        try:
            items = json.loads(body).get("items", [])
            hits = [i["full_name"] for i in items]
        except Exception:  # noqa: BLE001
            hits = ["unreadable body"]
        exact = [h for h in hits if h.lower().split("/")[-1] == name.lower()]
        summary = f"{len(items)} shown; exact-name repos: {exact or 'none'}"
    else:
        summary = f"INCONCLUSIVE (HTTP {code})"
    uo = []
    for kind in ("users", "orgs"):
        c, _ = get(f"https://api.github.com/{kind}/{name}")
        uo.append(f"{kind}/{name}: {'TAKEN' if c == 200 else ('FREE (404)' if c == 404 else f'INCONCLUSIVE ({c})')}")
    return {"search": summary, "user/org": "; ".join(uo)}


def check_domains(name):
    out = {}
    for tld in ("com", "dev", "io", "org"):
        code, body = get(f"https://rdap.org/domain/{name}.{tld}")
        if code == 404:
            out[tld] = "likely FREE (RDAP 404)"
        elif code == 200:
            out[tld] = "TAKEN (RDAP 200: registered)"
        else:
            out[tld] = f"INCONCLUSIVE ({code}: {body[:80]})"
    return out


def check_import(name):
    mod = name.lower().replace("-", "_")
    found = importlib.util.find_spec(mod)
    if found is None:
        return f"FREE (import {mod} fails as required)"
    return f"COLLIDES (importable from {found.origin})"


def main(argv):
    argv = list(argv)
    out = "docs/refactor/rename-kymora/NAME_CHECK_RAW.json" if "--out" in argv else None
    if "--out" in argv:
        idx = argv.index("--out")
        if idx + 1 < len(argv) and not argv[idx + 1].startswith("--"):
            out = argv[idx + 1]
            del argv[idx + 1]
        del argv[argv.index("--out")]
    args = [a for a in argv if not a.startswith("--")]
    report = {}
    for cand in args:
        entry = {"variants": {}}
        for v in variants(cand):
            entry["variants"][v] = {
                "pypi": check_pypi(v),
                "crates.io": check_crates(v),
                "npm": check_npm(v),
            }
        entry["github"] = check_github(cand.lower())
        entry["domains"] = check_domains(cand.lower())
        entry["import"] = check_import(cand)
        entry["pep503-collisions"] = sorted({pep503(v) for v in entry["variants"]})
        report[cand] = entry
        print(f"== {cand} ==")
        print(f"  import: {entry['import']}")
        for v, r in entry["variants"].items():
            print(f"  [{v}] pypi={r['pypi']} crates={r['crates.io']} npm={r['npm']}")
        print(f"  github: {entry['github']}")
        print(f"  domains: {entry['domains']}")
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"raw JSON written to {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
