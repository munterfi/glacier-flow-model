"""
Sub-level module 'fracd8' of the glacier-flow-model package.

The name 'fracd8' represents a modified version of the D8 algorithm for the
flow direction of the water surface algorithm, which is able to determine the
fraction of a cell that is moving based on an input velocity layer.

When moving in interations on a grid, there is a fundamental problem:
What happens when the distance of the movement in one iteration exceeds the
grid resolution?

In this case, the implemented solution will follow the flow in the cells via
the classified aspect until the necessary distance is reached. This neglects
the flow of other cells into the followed cells, which would have changed the
aspect and thereby the direction of flow. In addition, the performance is
worse. Therefore there are two versions in this submodule:

- fracd8_lim: Neglects the case described above (more performant) and thereby
  has a velocity of the resolution that must be considered.
- fracd8_inf: Follows the cells (in theory 'infinitely') in the case of large
  distances.
- fracd8: Decides after a check of the maxium velocity, which version to choose.

"""
from .flow import fracd8
from .infinite import fracd8_inf
from .limited import fracd8_lim

__all__ = ["fracd8", "fracd8_lim", "fracd8_inf"]
