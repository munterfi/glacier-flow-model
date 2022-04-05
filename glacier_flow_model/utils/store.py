from collections import defaultdict
from typing import Dict
from typing import List

import numpy as np


class ArrayStore:
    """Storage class for keeping track of arrays."""

    def __init__(self) -> None:
        self._container = defaultdict()  # type: Dict[str, LiFoStack]

    def create(self, key: str, size: int) -> None:
        self._container[key] = LiFoStack(size)

    def mean(self, key: str) -> np.ndarray:
        return np.nanmean(np.stack(self._container[key].all()), axis=0)

    def diff(self, key: str) -> np.ndarray:
        return np.nanmean(np.diff(np.stack(self._container[key].all()), axis=0), axis=0)

    def __getitem__(self, key: str) -> np.ndarray:
        return self._container[key].pop()

    def __setitem__(self, key: str, layer: np.ndarray) -> None:
        return self._container[key].push(layer)


class LiFoStack:
    """Last in – first out stack for numpy ndarrays."""

    def __init__(self, size: int) -> None:
        self.size = size
        self._stack = list()  # type: List[np.ndarray]

    def push(self, layer: np.ndarray) -> None:
        self._stack.append(np.copy(layer))
        if len(self._stack) > self.size:
            self._stack.pop(0)

    def pop(self) -> np.ndarray:
        return self._stack[-1]

    def all(self) -> List[np.ndarray]:
        return self._stack


"""
x = 4
y = 3
size = 3

layer1 = np.zeros([x,y]) + 1
layer2 = np.zeros([x,y]) + 2
layer3 = np.zeros([x,y]) + 3
layer4 = np.zeros([x,y]) + 4
layer5 = np.zeros([x,y]) + 5

store = ArrayStore()
store.create("u", 3)
store.create("h", 3)

store["h"] = layer1
store["h"]
store["h"] = layer2
store["h"]
store["h"] = layer3
store["h"] = layer4
store["h"]



#lifo1 = LiFoStore(x,y,size, type_=np.float32)

store = ArrayStore(x,y,size)
store.create("v", np.float32)
store.create("h", np.float32)

store["h"] = layer2
store["h"]
.add(layer2)
store["h"].add(layer3)
store["h"].get()

store["v"].add(layer4)
store["v"].add(layer2)
store["v"].add(layer5)
store["v"].get()

lifo.add(layer1)
lifo.add(layer2)
lifo.add(layer3)
lifo.add(layer4)
lifo.add(layer5)

shape=(0,250,2)

3DArray = np.vstack((3DArray,new2Darray.reshape(1,250,2)))

np.concatenate(layer, layer)
"""
