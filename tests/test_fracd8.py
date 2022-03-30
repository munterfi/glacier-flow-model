"""Tests for the GlacierFlowModel class."""
from glacier_flow_model.fracd8.flow import fracd8
from glacier_flow_model.fracd8.infinite import fracd8_inf
from glacier_flow_model.fracd8.limited import fracd8_lim
import numpy as np

# Globals
MAX_ITER = 50
CELL_RES = 200
X_SIZE = 358
Y_SIZE = 310
TOLERANCE = 0.05

# Setup
ELE = np.random.rand(Y_SIZE, X_SIZE) * 100
for x in range(X_SIZE):
    for y in range(Y_SIZE):
        ELE[y, x] = abs(y - (Y_SIZE / 2)) + abs(x - (X_SIZE / 2))

U = np.random.rand(Y_SIZE, X_SIZE) * 10
H = np.random.rand(Y_SIZE, X_SIZE) * 2
H_SUM = H.sum()


def test_fracd8_lim():
    u = np.copy(U)
    h = np.copy(H)
    for _ in range(MAX_ITER):
        ele = ELE + h
        h, asp = fracd8_lim(ele, u, h, CELL_RES)
    h_sum_lim = h.sum()
    diff = abs(H_SUM - h_sum_lim)
    assert (diff / H_SUM) < TOLERANCE


def test_fracd8_inf():
    u = np.copy(U)
    h = np.copy(H)
    for _ in range(MAX_ITER):
        ele = ELE + h
        h, asp = fracd8_inf(ele, u, h, CELL_RES)
    h_sum_inf = h.sum()
    diff = abs(H_SUM - h_sum_inf)
    assert (diff / H_SUM) < TOLERANCE


def test_fracd8():
    h_flow1, asp1, mode1 = fracd8(ELE, U * 1, H, CELL_RES)
    assert mode1 == "limited"
    h_flow2, asp2, mode2 = fracd8(ELE, U * CELL_RES, H, CELL_RES)
    assert mode2 == "infinite"
    assert (asp1 == asp2).all()
    assert (h_flow1 != h_flow2).any()
