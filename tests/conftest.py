"""Shared pytest fixtures / path setup for the S.A.R.A.L. test suite."""

import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TESTS_DIR)
_SCRAPER = os.path.join(_REPO_ROOT, "scraper")

for _p in (_REPO_ROOT, _SCRAPER):
    if _p not in sys.path:
        sys.path.insert(0, _p)
