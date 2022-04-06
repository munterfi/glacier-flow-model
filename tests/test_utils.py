"""Tests for `glacier_flow_model.utils` module."""
import numpy as np

from glacier_flow_model.utils.store import ArrayStore

X_RES = 4
Y_RES = 3
SIZE = 3
LAYER = "u"


def test_array_store():
    layer1 = np.zeros([X_RES, Y_RES]) + 1
    layer2 = np.zeros([X_RES, Y_RES]) + 2
    layer3 = np.zeros([X_RES, Y_RES]) + 3
    layer4 = np.zeros([X_RES, Y_RES]) + 4
    layer5 = np.zeros([X_RES, Y_RES]) + 5

    # Create store an initialize layer
    store = ArrayStore()
    store.create(LAYER, SIZE)

    # Adding layer to the stack
    store[LAYER] = layer1
    store[LAYER] = layer2
    store[LAYER] = layer3
    store[LAYER] = layer4
    store[LAYER] = layer5

    # Tests
    assert store["u"].mean() == 5
    assert store.mean("u").mean() == 4
