# ADR-0019: Test and benchmark policy

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The MVP needs a test policy that proves the contract and a benchmark policy
that establishes a performance baseline. The earlier baseline left coverage
thresholds, retry behavior, artifact retention, and regression thresholds open.

A numeric coverage threshold on a suite that does not yet exist would be
arbitrary. Automatic retries hide real failures, especially in a project that
must prove cross-language parity.

## Decision

Test policy:

- Coverage is measured by critical path, not by a numeric percentage. Every
  public builder method, node type, diagnostic code, serialization path,
  compiler failure mode, and asset rejection rule must be covered.
- CI never retries a failed test automatically. A flaky test is fixed or
  quarantined with an issue, and a quarantined test is reported separately
  from the pass/fail result.
- Test reports are retained as CI artifacts for 14 days.

Benchmark policy:

- The benchmark harness measures deserialization, validation, normalization,
  emission, compilation, and package size, with at least five repetitions.
- Wall time is the required metric, reported as median and p95. Peak memory
  is optional and measured on Linux only.
- Benchmark results are retained as CI artifacts for 90 days.
- A median wall-time regression of more than 10 percent against the stored
  baseline for the same fixture, stage, runtime, and platform produces a
  warning. It never fails the build in the MVP.

## Consequences

- The release gate depends on behavior coverage rather than a percentage that
  can be gamed.
- Flaky tests are visible instead of being hidden by retries.
- Performance regressions are reported early without blocking delivery before
  the baseline is stable.
- A numeric coverage threshold and a hard performance gate are Post-MVP
  decisions that require a stable baseline.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| A numeric coverage threshold | Arbitrary before the suite exists, and it measures lines rather than contract behavior. |
| Automatic test retries | Hides real failures and makes parity results unreliable. |
| A hard performance regression gate | Early baselines are noisy; false failures would block unrelated work. |
| No artifact retention | Failed runs would not be diagnosable after the job ends. |

## References

- `docs/development/testing.md`
- `docs/development/benchmarking.md`
- `TEST-014`, `TEST-015`, `TEST-024`
- `PERF-004`, `PERF-012`, `PERF-013`
