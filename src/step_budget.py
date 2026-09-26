'''Step budget limiter for agent loops.

An agent loop that never terminates burns money and time.  The step
budget caps total steps per task and optionally per phase (``plan``,
``act``, ``reflect``).  ``tick`` records a step; when a cap is hit the
limiter calls an overrun handler and reports ``exhausted`` so the loop
can wind down gracefully instead of being killed mid-thought.

``wind_down`` reserves the last N steps for summarization: once the
budget minus reserve is consumed, the agent should stop acting and only
summarize.  ``extend`` grants extra steps mid-run (e.g. after a
priority boost), and ``snapshot``/``restore`` checkpoint the counters.
'''

from __future__ import annotations


class StepBudget:
    '''Total + per-phase step caps with wind-down reserve.'''

    def __init__(self, max_steps, phase_quotas=None, reserve=0,
                 on_overrun=None):
        self.max_steps = max_steps
        self.phase_quotas = dict(phase_quotas or {})
        self.reserve = reserve
        self.on_overrun = on_overrun
        self.steps = 0
        self.phase_steps = {}
        self.overruns = 0

    def tick(self, phase="act"):
        '''Record one step; returns True when the budget is exhausted.'''
        self.steps += 1
        self.phase_steps[phase] = self.phase_steps.get(phase, 0) + 1
        exhausted = self.exhausted(phase)
        if exhausted:
            self.overruns += 1
            if self.on_overrun is not None:
                self.on_overrun(phase, self.steps)
        return exhausted

    def exhausted(self, phase=None):
        if self.steps >= self.max_steps:
            return True
        if phase is not None and phase in self.phase_quotas:
            return self.phase_steps.get(phase, 0) >= self.phase_quotas[phase]
        return False

    def should_wind_down(self):
        '''True when only reserve steps remain.'''
        return self.steps >= self.max_steps - self.reserve

    def remaining(self):
        return max(0, self.max_steps - self.steps)

    def remaining_phase(self, phase):
        quota = self.phase_quotas.get(phase)
        if quota is None:
            return self.remaining()
        return max(0, quota - self.phase_steps.get(phase, 0))

    def extend(self, extra_steps):
        '''Grant additional steps (e.g. after a priority boost).'''
        if extra_steps < 0:
            raise ValueError("cannot extend by a negative amount")
        self.max_steps += extra_steps
        return self.max_steps

    def progress(self):
        '''Fraction of the budget consumed, capped at 1.0.'''
        if self.max_steps <= 0:
            return 1.0
        return min(1.0, self.steps / self.max_steps)

    def allocate_phase(self, phase, quota):
        '''Set (or adjust) a phase quota; returns the quota.'''
        if quota < 0:
            raise ValueError("phase quota must be non-negative")
        self.phase_quotas[phase] = quota
        return quota

    def consume(self, steps, phase="act"):
        '''Record several steps; returns per-step exhausted flags.'''
        if steps < 0:
            raise ValueError("cannot consume negative steps")
        return [self.tick(phase) for _ in range(steps)]

    def is_critical(self, threshold=0.9):
        '''True when consumption has reached the threshold fraction.'''
        return self.progress() >= threshold

    def overrun_report(self):
        '''Overrun counts overall and per phase.'''
        return {"overruns": self.overruns, "steps": self.steps,
                "max_steps": self.max_steps,
                "remaining": self.remaining()}

    def phase_report(self):
        '''Per-phase steps, quotas, and remaining allowance.'''
        report = {}
        for phase, used in self.phase_steps.items():
            quota = self.phase_quotas.get(phase)
            report[phase] = {
                "steps": used, "quota": quota,
                "remaining": (max(0, quota - used) if quota is not None
                              else self.remaining()),
            }
        return report

    def snapshot(self):
        return {"max_steps": self.max_steps, "steps": self.steps,
                "phase_steps": dict(self.phase_steps),
                "overruns": self.overruns}

    def restore(self, snapshot):
        self.max_steps = snapshot["max_steps"]
        self.steps = snapshot["steps"]
        self.phase_steps = dict(snapshot["phase_steps"])
        self.overruns = snapshot["overruns"]

    def reset(self):
        self.steps = 0
        self.phase_steps = {}
        self.overruns = 0
