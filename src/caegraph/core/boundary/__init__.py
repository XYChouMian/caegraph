"""Semantic-region vocabulary: regions, declarations and the registry (ADR-018)."""

from caegraph.core.boundary.manager import BoundaryManager
from caegraph.core.boundary.region import BoundaryRegion
from caegraph.core.boundary.spec import BoundarySpec

__all__ = ["BoundaryManager", "BoundaryRegion", "BoundarySpec"]
