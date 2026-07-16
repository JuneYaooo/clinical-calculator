"""Manual clinical release allowlist.

Automated source checks are necessary but not sufficient. Add an ID only after
documented clinician review, source/version confirmation, validation cases, and
product approval. Keeping this list explicit prevents implementation work from
silently publishing a calculator for clinical use.
"""

CLINICALLY_RELEASED_IDS: frozenset[str] = frozenset()

__all__ = ["CLINICALLY_RELEASED_IDS"]
