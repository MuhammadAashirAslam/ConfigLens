"""Test suite for package initialization and versioning."""

import configlens


def test_version():
    """Verify package version is set to 0.1.0."""
    assert configlens.__version__ == "0.1.0"


def test_author():
    """Verify author metadata is set."""
    assert configlens.__author__ == "Muhammad Aashir Aslam"
