import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    ROOT / "apps" / "agent-api" / "src",
    ROOT / "packages" / "shared" / "src",
    ROOT / "packages" / "db" / "src",
    ROOT / "packages" / "llm-providers" / "src",
    ROOT / "packages" / "governance" / "src",
    ROOT / "packages" / "tools" / "src",
    ROOT / "packages" / "domain-services" / "src",
    ROOT / "packages" / "agent-core" / "src",
]
for p in PATHS:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
