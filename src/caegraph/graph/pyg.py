"""PyG backend adapter: CAEGraph to torch_geometric.data.Data (ADR-017/022).

The adapter is the Phase 2 backend adaptation slice. Its sole domain
input is a :class:`~caegraph.core.CAEGraph` canonical representation
(ADR-017; ADR-020 D4 — external field-value injection is
contract-excluded) and its sole obligation is the faithful
materialization of canonical attributes into the frozen Phase 2
node-graph schema (ADR-022 D-01..D-07). The adapter never re-decides
domain semantics: symmetric directed edge expansion belongs here
(ADR-019 C-01), while cell-to-node interpolation and every other
derived encoding belong to the transforms layer (gate 6).

Temporal organization is entirely upstream: explicit Snapshot
selection, candidate state, residual multiplicity disambiguation
(ADR-020 D6) and the single-state projection (ADR-023 D-08, ADR-024)
happen before adaptation, so this adapter implements no selector and
never reads ``timestep``, ``physical_time`` or Snapshots.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
from torch_geometric.data import Data  # type: ignore[import-untyped]

from caegraph.core import CAEGraph, NodeCategory

_NODE_CATEGORY_CODES: dict[NodeCategory, int] = {
    # ADR-022 D-07 explicit mapping — append-only: future node categories
    # may only append new integer values after the existing ones; the
    # existing mappings must never be reordered or changed.
    NodeCategory.INTERIOR: 0,
    NodeCategory.BOUNDARY: 1,
    NodeCategory.CORNER: 2,
}

_RESERVED_SCHEMA_KEYS = frozenset(
    {
        # Frozen Phase 2 schema keys (ADR-022 D-02).
        "edge_index",
        "num_nodes",
        "pos",
        "node_category",
        "field_families",
        # Common PyG attribute keys (ADR-022 D-04).
        "x",
        "y",
        "edge_attr",
        "batch",
        "ptr",
    }
)


def to_pyg_data(graph: CAEGraph) -> Data:
    """Materialize a CAEGraph as the Phase 2 PyG backend representation.

    The returned :class:`~torch_geometric.data.Data` carries exactly
    the frozen Phase 2 schema (ADR-022 D-02): ``edge_index`` — long
    ``[2, 2E]`` symmetric directed expansion of the canonical
    undirected pairs (``[2, 0]`` when edge-free, ADR-019 C-01);
    ``num_nodes`` — the graph's ``n_entities``; ``pos`` — topology
    node coordinates, float64 ``[n, 3]``; ``node_category`` — long
    codes via the D-07 explicit mapping; one key per materialized
    FieldData, keyed by its Field name; and ``field_families`` —
    always present, possibly empty (D-03/D-06), mapping every
    materialized field key to its ``node`` / ``cell`` association
    family. Declaration-only fields leave zero footprint — no key, no
    mapping entry, no fabricated values (D-06). Cell-family payloads
    are carried in original form: no implicit interpolation and no
    dtype cast (D-03/D-07).

    The node-graph backend profile (ADR-022 D-01, v1.3) is checked
    before anything is materialized. Its five decidable conditions are:
    ① the input is a :class:`~caegraph.core.CAEGraph`; ② the graph
    passes :meth:`CAEGraph.validate` — invoked directly, its exception
    system propagates verbatim; ③ a cell-based ``Mesh`` topology
    provider is attached; ④ ``topology.n_nodes == n_entities`` — a
    Phase 2 backend-profile condition only, never written back into
    :meth:`CAEGraph.validate`; ⑤ ``n_entities >= 1``. Adapter-owned
    profile checks raise :class:`ValueError`.

    Materialization additionally requires every FieldData payload to
    be losslessly representable as a ``torch.Tensor``. This is a Phase
    2 PyG backend-profile condition only: it restricts neither the
    backend-agnostic ``FieldData`` vocabulary nor the canonical
    legality of a CAEGraph state — unsupported payload forms simply
    fail fast at adaptation (D-01/D-03).

    Materialization is by-value: every tensor is built through
    ``torch.tensor``, which copies its input, so no returned tensor
    aliases canonical NumPy storage. Copying is the Stage 3 safety
    implementation choice, not an architecture contract; no cache is
    kept and no zero-copy pathway is used.

    Args:
        graph: CAEGraph canonical representation satisfying the
            node-graph backend profile.

    Returns:
        The materialized Phase 2 backend representation as a
        :class:`~torch_geometric.data.Data`.

    Raises:
        ValueError: If an adapter-owned profile check fails — a
            non-CAEGraph input; a missing topology provider;
            ``topology.n_nodes != n_entities``; ``n_entities < 1``; a
            Field name colliding with a reserved schema key (D-04);
            more than one FieldData realization for one Field (D-05 —
            the adapter implements no selection mechanism, ADR-020
            D6); or a FieldData payload that cannot be losslessly
            represented as a ``torch.Tensor`` (a PyG backend-profile
            condition; the canonical legality of the FieldData is
            unaffected). ``graph.validate()`` is invoked directly and
            its exceptions propagate verbatim.
    """
    if not isinstance(graph, CAEGraph):
        raise ValueError(
            "backend adapter domain input must be a CAEGraph canonical "
            "representation (ADR-022 D-01)"
        )
    graph.validate()
    topology = graph.topology
    if topology is None:
        raise ValueError(
            "node-graph backend profile requires a cell-based Mesh "
            "topology provider (ADR-022 D-01)"
        )
    if topology.n_nodes != graph.n_entities:
        raise ValueError(
            f"topology provider has {topology.n_nodes} nodes but the graph "
            f"counts {graph.n_entities} entities - the node-graph backend "
            "profile requires topology.n_nodes == n_entities (ADR-022 D-01)"
        )
    if graph.n_entities < 1:
        raise ValueError(
            "node-graph backend profile requires graph data with "
            "n_entities >= 1 (ADR-022 D-01)"
        )

    realization_counts: dict[str, int] = {}
    for data in graph.field_data:
        name = data.field.name
        realization_counts[name] = realization_counts.get(name, 0) + 1
    duplicated = sorted(name for name, count in realization_counts.items() if count > 1)
    if duplicated:
        raise ValueError(
            f"fields {duplicated} carry more than one FieldData "
            "realization; the adapter implements no selection mechanism "
            "(ADR-022 D-05, ADR-020 D6)"
        )

    # D-02: symmetric directed expansion of the canonical undirected
    # pairs (ADR-019 C-01) — long [2, 2E]; [2, 0] when edge-free.
    if graph.edges:
        undirected = np.asarray(graph.edges, dtype=np.int64)
        sources = np.concatenate([undirected[:, 0], undirected[:, 1]])
        targets = np.concatenate([undirected[:, 1], undirected[:, 0]])
        edge_index = torch.tensor(np.stack([sources, targets]), dtype=torch.long)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)

    pos = torch.tensor(np.asarray(topology.nodes), dtype=torch.float64)
    node_category = torch.tensor(
        [_NODE_CATEGORY_CODES[category] for category in graph.node_categories],
        dtype=torch.long,
    )

    payload: dict[str, Any] = {}
    field_families: dict[str, str] = {}
    for data in graph.field_data:
        name = data.field.name
        if name in _RESERVED_SCHEMA_KEYS:
            raise ValueError(
                f"field name {name!r} collides with a reserved PyG schema "
                "key; fail-fast at backend adaptation (ADR-022 D-04)"
            )
        # PyG backend-profile condition: the payload must be losslessly
        # representable as a torch Tensor. Unsupported backend-agnostic
        # payload forms fail fast here without touching canonical
        # legality (ADR-020 D4 vocabulary; ADR-022 D-01/D-03).
        try:
            payload[name] = torch.tensor(np.asarray(data.values))
        except (TypeError, ValueError, RuntimeError) as error:
            raise ValueError(
                f"field {name!r} payload cannot be materialized as a "
                "torch Tensor - a Phase 2 PyG backend profile condition; "
                "the canonical legality of the FieldData is unaffected "
                "(ADR-022 D-01/D-03)"
            ) from error
        field_families[name] = data.field.association

    return Data(
        edge_index=edge_index,
        num_nodes=graph.n_entities,
        pos=pos,
        node_category=node_category,
        **payload,
        field_families=field_families,
    )
