# Jev-cu Computer Use backend evaluation boundary

## Decision

This repository does not adopt or vendor Jev-cu in this change. It adds a conditional evaluation skill and a machine-checked comparison contract so Jev can be tested as a switchable decision backend when a compatible host runtime, provider account, and approved legal terms are available.

The default backend remains the host baseline. Jev is opt-in and dry-run by default. A Jev failure may return to baseline only after a fresh UI observation and the same local policy gate; an action with an uncertain outcome is never replayed automatically. Until the external runtime and benchmark evidence exist, the adoption result is `unresolved` and baseline remains enabled.

## Reviewed upstream evidence

The reviewed Jev-cu revision is `38fb31de7dfe6209bbe6e04057c00c6e885ba577` from [Sac-Y/Jev-cu](https://github.com/Sac-Y/Jev-cu/tree/38fb31de7dfe6209bbe6e04057c00c6e885ba577). The upstream README and source describe this path:

```text
Codex CUA observation
  -> AX/text candidate extraction
  -> Jev selects target, action, completion, and risk
  -> local policy gate
  -> Codex CUA execution
  -> fresh observation and verification
```

Relevant facts from the reviewed source:

| Area | Evidence | Harness boundary |
| --- | --- | --- |
| Data sent | The README says only text candidates are sent, not screenshots; `jev-decide.mjs` sends bounded context and candidates. | Keep the projection minimal, archive the local source observation, and redact secrets/private text before any provider call. |
| Runtime | The README runs `scripts/loop.mjs` inside Codex Desktop `cua_repl` with an injected CUA driver. | Treat this as an external runtime prerequisite; the harness does not claim Windows or a generic browser driver is compatible. |
| Provider | `TYPESAFE_API_KEY` is read from the environment or `.env.local`; the decision endpoint/model are defined in `jev-decide.mjs`. | Never add the key or private traces to this repository. Record provider terms, model, timeout, retry, and cost for each run. |
| Safety | The upstream README defaults to dry-run and lists delete, send, payment, authorization, upload, CAPTCHA, install, and system-settings actions as confirmation cases. | The host policy gate and human confirmation remain authoritative; an external decision is not an authorization. |
| Policy | `policy.mjs` contains an app allowlist, sensitive-label matching, confidence/risk thresholds, and escalation outcomes. | Re-check locally because policy text and candidate labels are untrusted input; test long/truncated labels and unknown apps. |
| Verification | `loop.mjs` supports a driver abstraction and a final verification callback. | Compare the same success predicate and retain raw traces for baseline and Jev. |
| License metadata | The reviewed `package.json` declares `ISC`; no `LICENSE` file is present in the reviewed repository tree. | Treat redistribution/adoption as legally unresolved until the upstream license and dependency/API terms are confirmed. Do not vendor or install it as part of this PR. |

The `package.json` and implementation links are kept in the [upstream source tree](https://github.com/Sac-Y/Jev-cu/tree/38fb31de7dfe6209bbe6e04057c00c6e885ba577). This is a static source review, not a claim that the API, desktop loop, or benchmark was executed here.

## Switch and fallback contract

The fixture `tests/fixtures/computer-use-backend-evaluation.json` defines two profiles:

- `baseline`: enabled by default and independent of Jev;
- `jev`: explicit candidate opt-in, same observation/driver/task conditions, and dry-run by default.

The adapter boundary is intentionally outside this repository's current runtime:

```text
backend_id=baseline|jev
  -> observe fresh UI state
  -> extract bounded candidates
  -> selected backend returns a typed decision
  -> validate target/action/confidence/risk
  -> local allowlist and sensitive-action gate
  -> execute one approved action
  -> observe fresh UI state and verify
```

The Jev profile falls back to baseline for candidate-unavailable, timeout, invalid-response, unknown-target, retry-budget, or uncertain-action-state events. The fallback procedure is:

1. Stop the Jev path and do not replay the last action.
2. Observe the UI again and determine whether the previous action took effect.
3. If the state is uncertain, escalate to the user.
4. Otherwise ask the baseline backend for a new decision and run the same local policy gate.
5. Verify the final state with the same task predicate and count the fallback.

An app allowlist, confirmation requirement, credential boundary, and CAPTCHA/authentication prohibition are host controls. Jev's output cannot bypass them.

## Controlled benchmark

The six representative tasks in the fixture cover reversible navigation, multi-step settings, disambiguation, modal recovery, instruction-like UI text, and sensitive confirmation. `modal-recovery` and `sensitive-confirmation` are hold-out tasks. Run baseline before Jev, keep task order and UI state equivalent, and freeze the driver, model/provider, runtime, timeout, retry policy, task revision, and resource limits.

Record raw per-trial values before aggregation:

- task success and capability score;
- critical failures, unsafe-action blocks, confirmation count, and fallback count;
- end-to-end latency, decision latency, wall-clock time, and step count;
- input/output tokens, observation bytes, model/tool calls, retries, and estimated cost;
- a local raw-trace reference with secrets removed.

Adoption requires a capability floor of `1.0`, zero critical-failure and unsafe-action regression, a positive predeclared hold-out latency improvement, equal conditions, and reproducible traces. Latency alone is insufficient. Missing CUA runtime, provider credentials, task environment, sample count, or legal/API confirmation produces `unresolved`, not adoption.

## Current residual

The harness can validate the protocol and fixture locally, but this environment does not provide approved Jev API credentials, a verified compatible Codex Desktop/macOS CUA runtime, an authorized upstream license/API-terms decision, or a completed representative GUI benchmark. Those items remain Issue #22 follow-up work. No external package was installed and no secret was written.

## Sources

- [Jev-cu reviewed revision](https://github.com/Sac-Y/Jev-cu/tree/38fb31de7dfe6209bbe6e04057c00c6e885ba577)
- [Jev-cu README](https://github.com/Sac-Y/Jev-cu/blob/38fb31de7dfe6209bbe6e04057c00c6e885ba577/README.md)
- [Jev-cu package manifest](https://github.com/Sac-Y/Jev-cu/blob/38fb31de7dfe6209bbe6e04057c00c6e885ba577/package.json)
- [Jev decision client](https://github.com/Sac-Y/Jev-cu/blob/38fb31de7dfe6209bbe6e04057c00c6e885ba577/scripts/jev-decide.mjs)
- [Jev policy gate](https://github.com/Sac-Y/Jev-cu/blob/38fb31de7dfe6209bbe6e04057c00c6e885ba577/scripts/policy.mjs)
- [Jev execution loop](https://github.com/Sac-Y/Jev-cu/blob/38fb31de7dfe6209bbe6e04057c00c6e885ba577/scripts/loop.mjs)
