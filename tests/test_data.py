#!/usr/bin/env python
"""Tests for `glacier_flow_model.data` module."""
from osgeo.gdal import Dataset

from glacier_flow_model.data import PkgDataAccess

pkg = PkgDataAccess(verbose=True)


def test_example_class():
    assert isinstance(pkg, PkgDataAccess)


def test_dem_example():
    assert isinstance(pkg.locate_dem(), str)
    assert isinstance(pkg.load_dem(), Dataset)
