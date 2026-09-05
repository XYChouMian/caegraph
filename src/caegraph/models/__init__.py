"""Model layer of CAEGraph — interface + utilities, no GNN zoo.

Planned (ADR-008/009, Phase 3): the ``Model(torch.nn.Module)`` contract
(encode-process-decode),
typing/protocols for CAE-aware models, and CAE-aware model utilities.
Concrete architectures (MeshGraphNet, GNO, Transformers...) live in
examples/ or external projects — never here.
"""
