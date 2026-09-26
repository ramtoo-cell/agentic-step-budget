# Step Budget Limiter for Agent Loops

Bounds agent loop iterations: max steps per task, per-phase step quotas, overrun callbacks, and graceful wind-down when the budget runs out.

**Stack:** Python 3.12 · stdlib only · unittest

## Problem statement

An agent loop that never terminates burns money and time.  The step budget caps total steps per task and optionally per phase (`plan`, `act`, `reflect`).  `tick` records a step; when a cap is hit the limiter calls an overrun handler and reports `exhausted` so the loop can wind down gracefully instead of being killed mid-thought.

## Design decisions

- `wind_down` reserves the last N steps for summarization: once the budget minus reserve is consumed, the agent should stop acting and only summarize.
- `extend` grants extra steps mid-run (e.g.
- after a priority boost), and `snapshot`/`restore` checkpoint the counters.

## Usage example

```python
from src.step_budget import StepBudget

b = StepBudget(max_steps=25, phase_quotas={"plan": 5}, reserve=3)
while not b.exhausted():
    b.tick("act")  # agent loop body here
print(b.steps)  # 25
```

## Layout

- `README.md`
- `src/step_budget.py`
- `tests/test_step_budget.py`
- `LICENSE`
- `.gitignore`

## Setup

No third-party dependencies — Python 3.11+ standard library only.

```bash
cd agentic-step-budget
python -m unittest discover -s tests -v
```

## License

MIT — see [LICENSE](LICENSE).
