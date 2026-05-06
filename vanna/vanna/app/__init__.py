"""App package — wires the locally cloned vanna source onto sys.path.

We do NOT pip-install vanna.  ``app/`` lives inside the cloned repo at
``vanna/vanna/app/``, so the vanna source is just one directory up at
``../src/``.  We prepend that path here so ``from vanna.legacy.<...> import
<...>`` resolves against the local copy in every entry point of this app.
"""

import sys
import pathlib

# app/ is at vanna/vanna/app/ → src is at vanna/vanna/src/
_VANNA_SRC = pathlib.Path(__file__).resolve().parent.parent / "src"

if _VANNA_SRC.exists() and str(_VANNA_SRC) not in sys.path:
    sys.path.insert(0, str(_VANNA_SRC))


def _ensure_vanna_path() -> None:
    """No-op getter so callers can ``from app import _ensure_vanna_path`` to
    guarantee the path-prepend side effect has run before they import vanna."""
    return None
