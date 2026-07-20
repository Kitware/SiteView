from pathlib import Path

from e3sm_siteview import __version__

__all__ = [
    "serve",
    "styles",
]

base_url = f"__e3sm_siteview_{__version__}"
serve_path = str(Path(__file__).with_name("serve").resolve())

serve = {base_url: serve_path}
styles = [f"{base_url}/style.css"]
scripts = [f"{base_url}/script.js"]
