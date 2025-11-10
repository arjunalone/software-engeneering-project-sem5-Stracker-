import re


def parse_requirements_txt(text: str):
    results = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"([A-Za-z0-9_\-.]+)\s*(.*)", line)
        if not m:
            continue
        name, spec = m.group(1), (m.group(2) or "").strip()
        if name.startswith("-e") or name.startswith("git+"):
            continue
        results.append({"name": name, "spec": spec})
    return results


def parse_pyproject_toml(content: bytes):
    try:
        try:
            import tomllib  # Py3.11+
        except Exception:
            import tomli as tomllib  # Py3.10 fallback
    except Exception:
        raise RuntimeError("tomllib/tomli missing; install tomli for Python 3.10")

    data = tomllib.loads(content.decode("utf-8", errors="ignore"))
    items = []
    poetry = (data.get("tool") or {}).get("poetry") or {}
    for name, spec in (poetry.get("dependencies") or {}).items():
        if name.lower() == "python":
            continue
        items.append({"name": name, "spec": spec if isinstance(spec, str) else ""})
    project = data.get("project") or {}
    for dep in project.get("dependencies", []) or []:
        m = re.match(r"([A-Za-z0-9_\-.]+)\s*(.*)", dep)
        if m:
            items.append({"name": m.group(1), "spec": (m.group(2) or "").strip()})
    return items
