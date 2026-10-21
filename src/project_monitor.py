"""Read-only production URL checks for registered LifeOS projects."""
import ipaddress, json, socket
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "state/projects"
OBSERVATIONS = ROOT / "state/observations"
TIMEOUT = (4, 8)
HEADERS = {"User-Agent": "LifeOS-ProjectMonitor/1.0", "Accept": "text/html,application/json,*/*"}


def check_url(url):
    parsed = urlparse(str(url))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        return {"status": "error", "severity": "high", "category": "production-health",
                "title": "Invalid production URL configuration", "url": str(url)[:200]}
    try:
        host = parsed.hostname.rstrip(".").lower()
        addresses = {item[4][0] for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
        if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
            return {"status": "error", "severity": "high", "category": "production-health",
                    "title": "Production URL resolves to a private or reserved address", "url": str(url)[:200]}
        response = requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=False)
        status = int(response.status_code)
        if status >= 500:
            severity, state = "high", "incident"
        elif status >= 400:
            severity, state = "medium", "incident"
        else:
            return {"status": "ok", "http_status": status, "url": url}
        return {"status": state, "severity": severity, "category": "production-health",
                "title": f"Production URL returned HTTP {status}", "http_status": status,
                "url": url}
    except (requests.RequestException, socket.gaierror, ValueError, OSError) as exc:
        return {"status": "incident", "severity": "high", "category": "production-health",
                "title": f"Production URL request failed ({type(exc).__name__})", "url": url}


def run():
    observations = []
    if PROJECTS.exists():
        for path in sorted(PROJECTS.glob("*/project.json")):
            try:
                project = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                observations.append({"status": "incident", "severity": "medium",
                    "category": "project-config", "title": f"Cannot parse {path.relative_to(ROOT)}"})
                continue
            url = str(project.get("published_url", "")).strip()
            if not url:
                continue
            result = check_url(url)
            result.update({"project": project.get("id", path.parent.name),
                           "project_name": project.get("name", path.parent.name),
                           "observed_at": datetime.now(timezone.utc).isoformat(),
                           "source": "LifeOS production URL monitor"})
            observations.append(result)
    OBSERVATIONS.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output = OBSERVATIONS / f"{day}.json"
    output.write_text(json.dumps(observations, indent=2) + "\n", encoding="utf-8")
    incidents = sum(1 for item in observations if str(item.get("status", "")).lower() not in {"ok", "healthy", "success"})
    print(f"Checked registered projects; samples={len(observations)}; incidents={incidents}; snapshot={output.relative_to(ROOT)}")
    return observations


if __name__ == "__main__":
    run()
