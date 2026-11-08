# Evaluation harness tests

Tests in this directory verify the independent evaluation harness using
synthetic fixtures. They cover structural validation, mandatory invariants,
semantic scoring, denominator preservation, and aggregate PASS/FAIL behavior.
They must exercise evaluator-owned validation and must not import application
validation functions as their oracle.

The future evaluation dataset is separate from these tests and requires at
least 15 reviewed meaningful cases, including an expected `Other` finding.
No evaluation cases or dataset are created by this README.
