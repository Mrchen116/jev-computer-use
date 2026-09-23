# Zoho invoice form demo

Real website: <https://www.zoho.com/invoice/free-invoice-generator.html>.
All data is synthetic. The task stops at a filled draft; it does not download,
send, save online, register an account, or initiate a payment.

This uses the Skill's **custom adapter workflow**, with live DOM observations
and a dedicated Playwright browser session. It is not a native-CUA regression or
a claim that an arbitrary website already has an adapter. No image recognition
or nested LLM is used inside the worker.

Final showcase: **20 fills in 59.50 seconds**, 41 Jev requests, no intermediate
LLM calls; all 32 final checks passed. Jev reported 329,495 input and 12,374 output
tokens. The [full recording](../../docs/media/zoho-invoice.mp4) is 59.32 seconds
at its original playback speed. See [all attempts](zoho-results.json).

## Decisions and execution

The host supplies the task and known input values, with their meanings. On each
step Jev first selects a field from the current rendered form, then selects the
literal input for that chosen field. All editable fields, including editable
labels, remain in the field menu. Code does not map desired values to fields or
choose a filling order. A short action scrolls, clicks, clears, types, and tabs
out; the read-back value is logged. Existing correct fields need no operation.

`zoho_verify.py` is a host-side oracle for this particular synthetic invoice. It
checks the final fields and the website-calculated amounts; it is never used to
choose an action or supply hints to Jev. Three populated lines must total USD 440,
with zero tax. Zoho's extra blank insertion row is allowed.

## Run

Use an installed Playwright CLI (the Codex Playwright skill's wrapper can install
it). Reusing that installed CLI avoids running npm package resolution per step.
Open a dedicated headed session and close the site's left navigation drawer if
it overlays the form. Start with a blank invoice and preserve other browser work.

```sh
playwright-cli -s=jev-zoho open https://www.zoho.com/invoice/free-invoice-generator.html --headed
# Close the navigation drawer using a fresh snapshot's control reference.
python evals/forms/zoho.py --state-dir /tmp/zoho-demo-new \
  --session jev-zoho --api-key-file /path/to/private-key-file
```

Alternatively set `TYPESAFE_API_KEY`. Use `--cli /path/to/playwright-cli` when
needed. Keep the state directory private and new for each attempt. It contains
`form.webm`, full requests/responses, compact live progress, and a summary with
final observations and verification. Create `STOP` in it for cancellation.
The runner has a 50-action / 600-second budget and yields on failed read-back.

## Lessons from the actual attempts

- HTML `select` elements do not define `readOnly`; normalize optional properties
  rather than assuming all fields have the input element shape.
- Zoho's date picker cleared values entered with `fill` when focus moved. Real
  keyboard events (`pressSequentially`) followed by Tab preserved the dates.
- Failed read-back must yield to the host. Repeating the same failed action can
  waste many decisions even when Jev keeps selecting the correct field/value.
- Close visible overlays and perform an actual click before typing. A successful
  DOM fill alone does not prove a user could interact with an unobscured control.

All earlier attempts are listed in `zoho-results.json`; private logs/videos are
retained locally. The showcased recording runs at normal speed, without cuts.
Host setup and iteration LLM costs are not measured; this is a demonstration,
not a controlled native-vs-Jev cost comparison.
