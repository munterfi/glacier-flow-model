"""Tests for the GlacierFlowModel class."""
from glacier_flow_model.data import PkgDataAccess
from glacier_flow_model.model import GlacierFlowModel

max_iter = 10
gfm = GlacierFlowModel(PkgDataAccess.locate_dem(), plot=False)
print(gfm)


def test_type():
    assert type(gfm) is GlacierFlowModel


def test_steady_state():
    gfm.reach_steady_state(max_years=max_iter)
    assert gfm.i == max_iter - 1


def test_simulate_positive_change():
    gfm.simulate(temp_change=10, max_years=max_iter)
    assert gfm.i == max_iter - 1


def test_simulate_negative_change():
    gfm.simulate(temp_change=-10, max_years=max_iter)
    assert gfm.i == max_iter - 1


def test_plot_destroy():
    gfm.plot = False
    assert gfm.plot is False
    assert gfm._fig is None


def test_plot_setup():
    gfm.plot = True
    assert gfm.plot is True
