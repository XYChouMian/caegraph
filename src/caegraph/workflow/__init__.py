"""Training workflow utilities of CAEGraph.

Planned (ADR-008, Phase 3): loss assembly (data + physics + observation
terms) and CAE-aware batch adaptation. No fit loop — training loops
belong to users (PyTorch / Lightning); caegraph adapts, never replaces.
"""
