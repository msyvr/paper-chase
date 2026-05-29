"""Mitigations subpackage.

Mitigations are configurable interventions on the publishing process. They hook
into the simulation loop at three well-defined points:

- ``constrain_action``: modify the agent's chosen action before it executes
  (e.g., pre-registration clamps ``qrp_intensity`` to 0).
- ``gate_publish``: decide whether (and how) a significant study result enters
  the literature (e.g., invariance requires significance across k contexts).
- ``post_step``: end-of-step bookkeeping (e.g., replication scans + retractions).

Mitigations compose by being applied in order via ``simulation.run(cfg,
mitigations=[...])``. ``constrain_action`` and ``gate_publish`` chain (each
mitigation sees the previous's output); ``post_step`` runs independently per
mitigation per step. Mitigations may carry state across calls (e.g., evidence
accumulators) and are constructed once per simulation run.

The three Phase-1 mitigations will each ship as a follow-up branch:

- ``pre_registration``: caps QRP at publication source.
- ``replication_retraction``: post-step scans + retracts on failed replication.
- ``invariance_requirement``: gates publication on k-context agreement.
"""
from .base import Mitigation, NoMitigation, StudyResult
from .pre_registration import PreRegistration
from .replication_retraction import ReplicationAndRetraction

__all__ = [
    "Mitigation",
    "NoMitigation",
    "PreRegistration",
    "ReplicationAndRetraction",
    "StudyResult",
]
