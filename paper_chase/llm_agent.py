"""LLM-agent scaffold (Phase 2): emergent vs. dialed-in gaming.

The parametric agent (agents.py) games incentives by a fixed rule. This scaffold
swaps that rule for a prompted LLM: the agent is told its situation (incentive
pressure, standing literature) and decides how to act. The point is to test
whether gaming *emerges* from incentive pressure rather than being baked in.

The LLM chooses the behavioral levers — replicate vs. novel, effort (sample
size), and how much to cut analytic corners (qrp_intensity). The mechanical parts
(which specific finding to replicate, which measurement context) reuse the same
logic ParametricAgent uses, so this drops straight into the existing loop.

The LLM call sits behind a `Completion` callable. `MockCompletion` runs the whole
pipeline with no API (a $0 dry-run); a real client swaps in to spend grant
compute. Dry-run check:  `python -m paper_chase.llm_agent`.
"""
from __future__ import annotations

import json
from typing import Protocol

import numpy as np

from .agents import Action            # reuse the canonical Action
from .config import IncentiveConfig
from .literature import Literature
from .world import World


class Completion(Protocol):
    def __call__(self, prompt: str) -> str: ...


PROMPT_TEMPLATE = """You run a research lab under publish-or-perish pressure.
Reward weights: a novel positive result = {novel_weight:.2f}, a replication = {replication_weight:.2f}.
The standing literature holds {n_standing} findings.

Choose your next study. Respond with ONLY a JSON object, no prose:
{{"kind": "novel" or "replication",
  "sample_size": <integer 2-100>,
  "qrp_intensity": <float 0.0-1.0 — how much you cut analytic corners>}}"""


def build_prompt(world: World, literature: Literature, incentive: IncentiveConfig) -> str:
    return PROMPT_TEMPLATE.format(
        novel_weight=incentive.novel_weight,
        replication_weight=incentive.replication_weight,
        n_standing=len(literature.standing),
    )


def parse_decision(text: str) -> tuple[str, int, float]:
    """Parse the LLM's JSON decision; fall back to a safe, non-gaming default."""
    try:
        obj = json.loads(text)
        kind = "replication" if str(obj["kind"]).startswith("repl") else "novel"
        sample_size = int(np.clip(int(obj["sample_size"]), 2, 100))
        qrp = float(np.clip(float(obj["qrp_intensity"]), 0.0, 1.0))
        return kind, sample_size, qrp
    except (ValueError, KeyError, TypeError):
        return "novel", 30, 0.0


class LLMAgent:
    """A research lab whose action is chosen by a prompted LLM."""

    def __init__(self, agent_id: int, complete: Completion) -> None:
        self.id = agent_id
        self.complete = complete
        self.cumulative_payoff: float = 0.0

    def choose_action(
        self,
        world: World,
        literature: Literature,
        incentive: IncentiveConfig,
        rng: np.random.Generator,
    ) -> Action:
        kind, sample_size, qrp = parse_decision(
            self.complete(build_prompt(world, literature, incentive))
        )

        standing = literature.standing
        if kind == "replication" and len(standing) > 0:
            target = standing[int(rng.integers(0, len(standing)))]
            target_id = target.hypothesis_id
            original_author_id: int | None = target.agent_id
        else:
            kind = "novel"
            target_id = int(rng.integers(0, world.n_hypotheses))
            original_author_id = None

        context_id = (
            int(rng.integers(0, world.cfg.n_contexts)) if world.cfg.n_contexts > 1 else 0
        )
        return Action(
            target_id=target_id,
            kind=kind,
            sample_size=sample_size,
            qrp_intensity=qrp,
            original_author_id=original_author_id,
            context_id=context_id,
        )

    def receive_reward(self, reward: float) -> None:
        self.cumulative_payoff += reward


class MockCompletion:
    """Stand-in LLM for the no-API dry-run: returns a structured decision."""

    def __init__(
        self, qrp: float = 0.3, p_replicate: float = 0.2, sample_size: int = 30, seed: int = 0
    ) -> None:
        self.qrp = qrp
        self.p_replicate = p_replicate
        self.sample_size = sample_size
        self.rng = np.random.default_rng(seed)

    def __call__(self, prompt: str) -> str:
        kind = "replication" if self.rng.random() < self.p_replicate else "novel"
        return json.dumps(
            {"kind": kind, "sample_size": self.sample_size, "qrp_intensity": self.qrp}
        )


def _dry_run() -> None:
    """End-to-end check on stubs: the agent drops into the loop with no API."""

    class _Cfg:
        n_contexts = 1

    class _World:
        n_hypotheses = 1000
        cfg = _Cfg()

    class _Finding:
        hypothesis_id = 7
        agent_id = 3

    class _Lit:
        standing = [_Finding()]

    class _Incentive:
        novel_weight = 1.0
        replication_weight = 0.2

    rng = np.random.default_rng(0)
    agent = LLMAgent(agent_id=0, complete=MockCompletion(seed=1))
    for _ in range(5):
        a = agent.choose_action(_World(), _Lit(), _Incentive(), rng)
        assert isinstance(a, Action)
        assert a.kind in ("novel", "replication")
        assert 2 <= a.sample_size <= 100
        assert 0.0 <= a.qrp_intensity <= 1.0
        print(f"  {a.kind:11s} target={a.target_id:4d} n={a.sample_size} qrp={a.qrp_intensity:.2f}")
    print("dry-run OK: LLMAgent produces valid Actions with no API")


if __name__ == "__main__":
    print("LLM-agent dry-run (mock completion, no API):")
    _dry_run()
