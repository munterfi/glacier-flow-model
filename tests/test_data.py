"""Tests for `glacier_flow_model.data` module."""
from rasterio import DatasetReader

from glacier_flow_model.data import PkgDataAccess

pkg = PkgDataAccess()


def test_example_class():
    assert isinstance(pkg, PkgDataAccess)


def test_dem_example():
    assert isinstance(PkgDataAccess.locate_dem(), str)
    assert isinstance(PkgDataAccess.load_dem(), DatasetReader)
