# Evidence-Bound AI Assistant

QS-DMSS includes an optional, provider-agnostic model sidecar for four bounded
research-support tasks:

1. evidence summary;
2. claim-boundary review;
3. comparison critique; and
4. next-experiment proposals.

The sidecar is disabled by default. Deterministic Research Runbook guidance
continues to work without a model.

## Scientific and Execution Boundary

The model is advisory and read-only. It cannot:

- launch, replay, or modify a run;
- call QS-DMSS tools or external sources;
- alter a run, comparison, manifest, or measured evidence bundle;
- authorize compute, provider spend, or publication; or
- establish physical validity, peer review, or scientific truth.

The browser submits only an approved task plus scenario, run, and comparison
identifiers. The server resolves those identifiers and constructs a field-level
allowlist from recorded QS-DMSS artifacts. Arbitrary browser-supplied context is
rejected.

Each successful response becomes a separate `ai-interactions/<interaction-id>`
advisory artifact with:

- the source artifact IDs, kinds, and SHA-256 hashes;
- provider, model, endpoint scope, timestamps, request/context/response hashes,
  parameters, and token counts when supplied;
- the validated draft and artifact-level citations;
- a human disposition of accepted, edited, or rejected;
- an append-only review history within the interaction record; and
- its own checksum manifest and downloadable advisory bundle.

The original evidence manifest is never rewritten to include the AI artifact.

## Provider Contract

QS-DMSS uses a small internal provider protocol and ships one adapter for the
OpenAI-compatible chat-completions JSON contract. This keeps provider choice
outside the cockpit UI and avoids a vendor SDK dependency. A controlled local
runtime, self-hosted gateway, or hosted service can be used if it exposes that
contract.

The adapter requires a structured JSON response containing a title, draft,
artifact-cited findings, limitations, and proposed actions. QS-DMSS rejects a
response when it:

- is not valid JSON or exceeds the response size limit;
- violates the bounded response schema or text limits;
- cites an artifact outside the server-selected context; or
- introduces a numerical token in an asserted finding that does not occur in
  the recorded context.

Redirects are not followed. Remote endpoints require HTTPS and a separate
operator acknowledgement. Provider failures and rejected responses create no
advisory artifact.

## Local Configuration

Set the following variables in the process that starts the cockpit:

```powershell
$env:QS_DMSS_AI_ENABLED = "1"
$env:QS_DMSS_AI_BASE_URL = "http://127.0.0.1:11434/v1"
$env:QS_DMSS_AI_MODEL = "your-controlled-model-id"
qs-dmss cockpit --host 127.0.0.1 --port 8001
```

An API key is optional and is read only from `QS_DMSS_AI_API_KEY`. Do not place
credentials in the endpoint URL, repository, browser, or saved study data.

Optional settings:

| Variable | Purpose | Default |
| --- | --- | --- |
| `QS_DMSS_AI_PROVIDER_LABEL` | Human-readable provenance label | `OpenAI-compatible` |
| `QS_DMSS_AI_TIMEOUT_SECONDS` | Request timeout from 1 to 180 seconds | `45` |
| `QS_DMSS_AI_JSON_MODE` | Request provider JSON-object mode | `1` |

If a controlled endpoint does not implement `response_format`, set
`QS_DMSS_AI_JSON_MODE=0`; the returned content must still be a valid response
object under the QS-DMSS schema.

## Remote and Hosted Configuration

A non-loopback endpoint is rejected unless all of the following are true:

- the endpoint uses HTTPS;
- `QS_DMSS_AI_ALLOW_REMOTE=1` is set; and
- the operator has reviewed the provider's retention, training, residency,
  access-control, and incident-response terms.

Only the allowlisted evidence context is transmitted, but that context can
still contain unpublished measurements and research metadata. The acknowledgement
is a disclosure gate, not a confidentiality guarantee.

The public hosted-demo mode adds another independent gate. Model drafts remain
off unless `QS_DMSS_AI_HOSTED_ENABLED=1` is also set. Enabling this setting
should be treated as a production data-governance decision, with authentication,
rate limits, budget limits, abuse monitoring, and a documented provider policy.

## Human Review Workflow

1. Select one of the four approved tasks in the contextual Evidence Assistant.
2. Record the run or guided comparison required by that task.
3. Generate the model draft.
4. Inspect every finding and artifact citation.
5. Enter the reviewer identity and accept, edit, or reject the draft.
6. Download the advisory bundle when the disposition needs to travel with a
   review packet.

Acceptance records a human disposition; it does not convert the draft into
measured evidence. Edited wording is preserved separately from the original
model response.

## Known Limitations

Schema, citation, and numeric checks reduce obvious fabrication; they do not
prove that a statement correctly interprets an artifact. Citations are bound to
artifact identities rather than exact JSON fields. Models can omit relevant
evidence, misunderstand methodology, or produce plausible but weak proposals.
Human scientific review therefore remains mandatory, and deterministic source
artifacts remain authoritative.
