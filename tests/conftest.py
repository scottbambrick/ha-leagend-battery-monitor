"""Load the integration's plain-Python modules without Home Assistant.

The package's __init__.py imports Home Assistant, so the package is
registered here by path instead.
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "custom_components.leagend_ble"

sys.modules.setdefault(
    "custom_components", types.ModuleType("custom_components")
)
_pkg = types.ModuleType(PACKAGE)
_pkg.__path__ = [str(ROOT / "custom_components" / "leagend_ble")]
sys.modules[PACKAGE] = _pkg
