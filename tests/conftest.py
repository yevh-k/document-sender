"""Isolate mail-engine unit tests from the Home Assistant runtime package."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

_COMPONENT_PATH = Path(__file__).parents[1] / "custom_components" / "document_sender"
_PACKAGE_NAME = "custom_components.document_sender"

# These are pure unit tests. Supplying the package path avoids executing integration
# setup while still exercising the production mailer, image, models, and constants.
if _PACKAGE_NAME not in sys.modules:
    package = ModuleType(_PACKAGE_NAME)
    package.__dict__["__path__"] = [str(_COMPONENT_PATH)]
    sys.modules[_PACKAGE_NAME] = package
