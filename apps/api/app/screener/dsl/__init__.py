"""Scan expression language: AST, parser, validator, compiler, evaluator,
registry, serializer (master prompt §14 "SCAN LANGUAGE — CORE REQUIREMENT").

Additive to `app.services.condition_evaluator`, which keeps serving the 13
prebuilt scans unchanged — see docs/ARCHITECTURE_AUDIT.md and the Phase 3.1
plan for why this is a new package rather than a rewrite of a working one.
"""
