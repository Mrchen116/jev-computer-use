"""Recorded Zoho form demo using live DOM fields and two dependent Jev choices.

Custom Playwright adapter, not the default native Computer Use runner.
Start a dedicated browser session at the target URL before running.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from zoho_verify import verify

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "skills/jev-computer-use/scripts"))
from jev_computer_use.models import JevClient  # noqa: E402 - load bundled skill client

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--state-dir", type=Path, required=True)
parser.add_argument("--cli", default="playwright-cli")
parser.add_argument("--session", default="jev-zoho")
parser.add_argument("--api-key-file", type=Path)
args = parser.parse_args()
root = args.state_dir
root.mkdir(parents=True, exist_ok=True)
cli = args.cli


def cmd(*a):
    p = subprocess.run(
        [cli, "-s=" + args.session, *a], capture_output=True, text=True, timeout=60
    )
    if p.returncode or "### Error" in p.stdout:
        raise RuntimeError(p.stdout + p.stderr)
    return p.stdout


obs = Path(__file__).with_name("zoho-observe.js").read_text()


def observe():
    return json.loads(
        cmd("run-code", "async(page)=>await page.evaluate(" + obs + ")", "--raw")
    )


inputs = {
    "company": ("Jev Demo Studio", "seller company"),
    "contact": ("Demo Operator", "seller contact name"),
    "seller_address": ("100 Example Avenue", "seller street"),
    "seller_city": ("Example City", "seller city"),
    "country": (
        "U.S.A",
        "seller and customer country United States; existing U.S.A is correct",
    ),
    "customer": ("Sample Client LLC", "customer company"),
    "customer_address": ("200 Sample Street", "customer street"),
    "customer_city": ("Sample City", "customer city"),
    "number": ("DEMO-20260923", "invoice number"),
    "date": ("Sep 23, 2026", "invoice issue date"),
    "due": ("Oct 23, 2026", "invoice due date"),
    "item1": ("Interface review", "first line description"),
    "qty1": ("2", "first line quantity"),
    "rate1": ("120", "first line unit rate"),
    "item2": ("Documentation", "second line description"),
    "qty2": ("3", "second line quantity"),
    "rate2": ("40", "second line unit rate"),
    "item3": ("Demo preparation", "third line description"),
    "qty3": ("1", "third line quantity"),
    "rate3": ("80", "third line unit rate"),
    "tax": ("0", "all line tax rates zero"),
    "notes": ("DEMONSTRATION ONLY - NOT PAYABLE", "invoice notes"),
    "terms": ("Synthetic data for a software demonstration.", "terms and conditions"),
}
texts = {k: {"text": v[0], "purpose": v[1]} for k, v in inputs.items()}
task = "Fill the invoice using all supplied values. Three line items in the stated order, zero tax, USD total 440 (already calculated by host). Preserve labels and currency. Existing correct values need no edit. Only fill the on-page draft; do not download, print, save online, send, sign up or add payments. Finish once all required values are present."
key = (
    args.api_key_file.read_text().strip()
    if args.api_key_file
    else os.environ["TYPESAFE_API_KEY"]
)
client = JevClient(key)
history = []
start = time.monotonic()
reason = "budget"
s = None


def ask(state, question, criteria):
    payload = {
        "model": "jev-latest",
        "state": state,
        "questions": {
            "choice": {
                "type": "choice",
                "instructions": [question],
                "criteria": criteria,
            }
        },
    }
    ans, secs = client.ask(payload)
    with (root / "history.jsonl").open("a") as f:
        f.write(json.dumps({"request": payload, "answer": ans, "seconds": secs}) + "\n")
    return ans["answers"]["choice"]["choice"], secs


cmd("video-start", str(root / "form.webm"), "--size=1280x900")
try:
    for step in range(50):
        if (root / "STOP").exists():
            reason = "host_stop"
            break
        if time.monotonic() - start > 600:
            break
        s = observe()
        if s["url"] != "https://www.zoho.com/invoice/free-invoice-generator.html":
            raise RuntimeError("Target changed")
        fields = {
            f"f{i}": f
            for i, f in enumerate(s["fields"])
            if f["id"] and not f["readonly"] and not f["disabled"]
        }
        state = {
            "task": task,
            "input_texts": texts,
            "observation": s,
            "history": history,
            "warnings": [],
        }
        criteria = {
            k: "Edit " + json.dumps(v, ensure_ascii=False) for k, v in fields.items()
        }
        criteria.update(
            done="All requested values are present; yield for host verification",
            help="Cannot continue with these fields and input values; ask host",
        )
        choice, sec = ask(
            state,
            "Which field should be filled next? Choose a field whose current value does not yet match the task. Field labels are editable too; preserve them.",
            criteria,
        )
        if choice in ("done", "help"):
            reason = choice
            break
        field = fields[choice]
        state["selected_field"] = field
        value, sec2 = ask(
            state,
            "Which supplied literal value belongs in the selected field?",
            {
                **{k: json.dumps(v) for k, v in texts.items()},
                "help": "No available value matches this field",
            },
        )
        if value == "help":
            reason = "help_input"
            break
        action = {"id": field["id"], "text": texts[value]["text"]}
        code = """async(page)=>{const a=ACTION;const loc=page.locator('[id='+JSON.stringify(a.id)+']');await loc.scrollIntoViewIfNeeded();await loc.click();await loc.fill('');await loc.pressSequentially(a.text);await loc.press('Tab');return {value:await loc.inputValue()};}""".replace(
            "ACTION", json.dumps(action)
        )
        result = json.loads(cmd("run-code", code, "--raw"))
        event = {
            "step": step + 1,
            "field": field["id"],
            "input": value,
            "value": result["value"],
            "outcome": "succeeded"
            if result["value"] == action["text"]
            or result["value"] == action["text"] + ".00"
            else "changed_format_or_failed",
            "jev_s": sec + sec2,
        }
        history.append(event)
        (root / "progress.json").write_text(
            json.dumps(
                {
                    "phase": "filling",
                    "history": history,
                    "history_location": str(root / "history.jsonl"),
                }
            )
        )
        print(json.dumps(event), flush=True)
        if event["outcome"] != "succeeded":
            reason = "execution_help"
            break
except Exception as e:
    reason = "error"
    print(repr(e), flush=True)
    raise
finally:
    try:
        s = observe()
        (root / "summary.json").write_text(
            json.dumps(
                {
                    "reason": reason,
                    "seconds": time.monotonic() - start,
                    "calls": client.calls,
                    "usage": client.usage,
                    "events": client.events,
                    "history": history,
                    "final": s,
                    "verification": verify(s),
                },
                indent=2,
            )
        )
    finally:
        client.close()
        cmd("video-stop")
    print("FINAL", reason, flush=True)
