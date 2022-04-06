"""Tests for `glacier_flow_model.fracd8` module."""
import numpy as np

from glacier_flow_model.fracd8.direction import classify_aspect
from glacier_flow_model.fracd8.direction import position
from glacier_flow_model.fracd8.flow import fracd8
from glacier_flow_model.fracd8.infinite import fracd8_inf
from glacier_flow_model.fracd8.limited import fracd8_lim

# Globals
MAX_ITER = 10
CELL_RES = 200
X_SIZE = 50
Y_SIZE = 50
TOLERANCE = 0.10

# Setup
ELE = np.random.rand(Y_SIZE, X_SIZE) * 100
for x in range(X_SIZE):
    for y in range(Y_SIZE):
        ELE[y, x] = abs(y - (Y_SIZE / 2)) + abs(x - (X_SIZE / 2))

U = np.random.rand(Y_SIZE, X_SIZE) * 10
H = np.random.rand(Y_SIZE, X_SIZE) * 2
H_SUM = H.sum()


def test_fracd8_position():
    assert (0, 0) == position.py_func(0, 0, 0)
    assert (1, 1) == position.py_func(0, 0, 1)
    assert (0, 1) == position.py_func(0, 0, 2)
    assert (-1, 1) == position.py_func(0, 0, 3)
    assert (-1, 0) == position.py_func(0, 0, 4)
    assert (-1, -1) == position.py_func(0, 0, 5)
    assert (0, -1) == position.py_func(0, 0, 6)
    assert (1, -1) == position.py_func(0, 0, 7)
    assert (1, 0) == position.py_func(0, 0, 8)


def test_fracd8_classify_aspect():
    asp = classify_aspect.py_func(ELE)
    assert asp.min() == 0
    assert asp.max() == 8


def test_fracd8_lim():
    u = np.copy(U)
    h = np.copy(H)
    for _ in range(MAX_ITER):
        ele = ELE + h
        h, asp = fracd8_lim.py_func(ele, u, h, CELL_RES)
    h_sum_lim = h.sum()
    diff = abs(H_SUM - h_sum_lim)
    assert (diff / H_SUM) < TOLERANCE


def test_fracd8_inf():
    u = np.copy(U)
    h = np.copy(H)
    for _ in range(MAX_ITER):
        ele = ELE + h
        h, asp = fracd8_inf.py_func(ele, u, h, CELL_RES, 5)
    h_sum_inf = h.sum()
    diff = abs(H_SUM - h_sum_inf)
    assert (diff / H_SUM) < TOLERANCE


def test_fracd8():
    h_flow1, asp1, mode1 = fracd8.py_func(ELE, U * 1, H, CELL_RES)
    assert mode1 == "limited"
    h_flow2, asp2, mode2 = fracd8.py_func(ELE, U * CELL_RES, H, CELL_RES)
    assert mode2 == "infinite"
    assert (asp1 == asp2).all()
    assert (h_flow1 != h_flow2).any()
