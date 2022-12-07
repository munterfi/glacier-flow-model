from collections import defaultdict
from typing import Dict  # noqa: F401
from typing import List  # noqa: F401

import numpy as np


class ArrayStore:
    """Storage class for keeping track of arrays."""

    def __init__(self) -> None:
        self._container = defaultdict()  # type: Dict[str, LiFoStack]

    def __repr__(self) -> str:
        return "ArrayStore()"

    def create(self, key: str, size: int) -> None:
        self._container[key] = LiFoStack(size)

    def mean(self, key: str) -> np.ndarray:
        return np.nanmean(self._container[key].all(), axis=0)

    def diff(self, key: str) -> np.ndarray:
        return np.nanmean(np.diff(self._container[key].all(), axis=0), axis=0)

    def __getitem__(self, key: str) -> np.ndarray:
        return self._container[key].pop()

    def __setitem__(self, key: str, layer: np.ndarray) -> None:
        return self._container[key].push(layer)


class LiFoStack:
    """Last in first out stack for numpy ndarrays."""

    def __init__(self, size: int) -> None:
        self.size = size
        self._stack = list()  # type: List[np.ndarray]

    def __repr__(self) -> str:
        return f"LiFoStack(size={self.size})"

    def push(self, layer: np.ndarray) -> None:
        self._stack.append(np.copy(layer))
        if len(self._stack) > self.size:
            self._stack.pop(0)

    def pop(self) -> np.ndarray:
        return self._stack[-1]

    def all(self) -> np.ndarray:
        return np.stack(self._stack)
