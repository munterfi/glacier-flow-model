#!/usr/bin/env python

"""Tests for the GlacierFlowModel class."""

from glacier_flow_model.model import GlacierFlowModel

max_iter = 10
gfm = GlacierFlowModel('data/dem.tif')


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