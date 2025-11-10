import re
import requests
import logging

PYPI_JSON = "https://pypi.org/pypi/{name}/json"


def enrich_from_pypi(name: str) -> dict:
    try:
        resp = requests.get(PYPI_JSON.format(name=name), timeout=10)
        if resp.status_code != 200:
            return {}
        j = resp.json()
        info = j.get("info", {})
        releases = j.get("releases", {})
        latest = info.get("version")
        urls = info.get("project_urls") or {}
        homepage = info.get("home_page") or urls.get("Homepage")
        repo_url = None
        preferred_keys = {k.lower() for k in [
            "Source", "Source Code", "Repository", "Code", "Home", "Homepage"
        ]}
        for k, v in urls.items():
            if k.lower() in preferred_keys and v:
                repo_url = v
                break
        if not repo_url:
            for v in urls.values():
                if not v:
                    continue
                if re.search(r"(github|gitlab|bitbucket)\.com/[^\s]+", v, re.IGNORECASE):
                    repo_url = v
                    break
        release_date = None
        if latest and latest in releases and releases[latest]:
            f = releases[latest][0]
            release_date = f.get("upload_time_iso_8601") or f.get("upload_time")
        return {
            "latest_version": latest,
            "release_date": release_date,
            "homepage": homepage,
            "repo_url": repo_url,
            "pypi_url": f"https://pypi.org/project/{name}/",
        }
    except Exception as e:
        logging.warning("PyPI enrich failed for %s: %s", name, str(e))
        return {}
