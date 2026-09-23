"""Full native observations and concrete actions for the general task loop."""

import json
import re

from .desktop import nodes


def describe_window(raw, application, applications):
    """Preserve the complete AX text; parse only what execution needs."""
    focus = re.search(r"The focused UI element is (\d+)\b", raw)
    focused = focus[1] if focus else None
    controls = {}
    parsed = nodes(raw)
    for index, node in enumerate(parsed):
        if "(disabled)" in node["detail"]:
            continue
        label = re.sub(r"^(?:\([^)]*\)\s*)+", "", node["detail"])
        name = re.split(r"(?:^|, )(?:Value|URL|Placeholder|Help|Secondary Actions):", label)[0]
        if not name:
            placeholder = re.search(r"(?:^|, )Placeholder: (.*?)(?=, (?:Value|URL|Help|Secondary Actions):|$)", label)
            name = placeholder[1] if placeholder else ""
        value = re.search(r"(?:^|, )Value: (.*?)(?=, (?:Placeholder|URL|Help):|$)", label, re.S)
        controls[node["ref"]] = {
            "id": node["ref"], "role": node["role"], "name": name,
            "value": value[1] if value else "",
            "settable": bool(re.search(r"\([^)]*\bsettable\b[^)]*\)", node["detail"])),
        }
        # AX often leaves a field unnamed while exposing its label as a sibling.
        # Quote that structural fact; do not invent a semantic label or UI route.
        previous = parsed[index - 1] if index else None
        if (node["role"] == "textbox" and previous
                and previous["role"] in ("text", "heading")
                and previous["depth"] == node["depth"]):
            controls[node["ref"]]["preceding_text"] = previous["detail"]
    return {
        "application": application, "applications": applications,
        "window": raw.splitlines()[0] if raw else "",
        "focused_element": focused, "ui_tree": raw,
        "controls": controls,
    }


def action_menu(observation, input_texts):
    """Build executable options without predicting a task's UI route."""
    def context(control):
        text = control.get("preceding_text")
        return f". Immediately preceding AX sibling text: {text!r}" if text else ""

    actions = {}
    for app in observation["applications"]:
        if app["id"] != observation["application"]:
            actions["app_" + app["id"]] = {
                "type": "switch_app", "application": app["id"],
                "label": "Switch to application: " + app["name"],
            }
    for ref, control in observation["controls"].items():
        target = {k: control[k] for k in ("id", "role", "name")}
        # Re-focusing the already focused field is not a next input operation.
        # Offering it caused Jev to loop instead of asking the host for text.
        needs_focus = control["role"] != "textbox" or ref != observation["focused_element"]
        # Native click can address text too. Custom buttons and autocomplete
        # options often expose only AX static text, without a button/link role.
        clickable = control["role"] in ("button", "link", "checkbox", "radio", "tab", "menuitem", "textbox") or (control["role"] == "text" and bool(control["name"]))
        if needs_focus and clickable:
            actions["click_" + ref] = {
                "type": "click", "target": target,
                "label": f"Click {control['role']} {ref}: {control['name']}" + context(control),
            }
        if control["role"] in ("scrollarea", "webarea"):
            for direction in ("up", "down", "left", "right"):
                actions[f"scroll_{ref}_{direction}"] = {
                    "type": "scroll", "target": target, "direction": direction,
                    "label": f"Scroll {direction} in {ref}: {control['name']}",
                }
    focused = observation["controls"].get(observation["focused_element"])
    if focused and focused["role"] == "textbox" and focused["settable"]:
        target = {k: focused[k] for k in ("id", "role", "name")}
        for text_id, item in input_texts.items():
            for mode in ("replace", "insert"):
                actions[f"{mode}_{text_id}"] = {
                    "type": mode, "target": target, "text_id": text_id,
                    "text": item["text"],
                    "label": f"{mode.title()} text in focused field {target['id']} ({target['name']})" + context(focused) + f" using input_texts[{text_id!r}].text exactly. Purpose: {item['purpose']}. Do not submit.",
                }
        actions["help_input"] = {
            "type": "help_input", "target": target,
            "label": f"Ask the outer agent for the exact text needed in focused field {target['id']}: {target['name']}" + context(focused),
        }
    if observation["application"]:
        for key in ("Return", "Escape", "Tab", "Up", "Down", "Left", "Right", "space", "super+a"):
            actions["key_" + key] = {"type": "key", "key": key, "label": f"Press {key} at the current focus"}
    actions.update({
        "wait": {"type": "wait", "label": "Wait for the next observation"},
        "help_reasoning": {"type": "help_reasoning", "label": "Ask the outer agent for reasoning, clarification or an operation not available in this menu"},
        "review_completion": {"type": "review_completion", "label": "Pause for outer review: the whole task has its result or a terminal outcome (success or failure). Do not retry or reset it yourself."},
    })
    return actions


class Computer:
    """Use the installed CUA transport without a browser-specific state model."""

    def __init__(self, native, application=None):
        self.native = native
        self.application = application
        self.bound = None

    def _json(self, expression):
        result = self.native.js('nodeRepl.write("JEV_FULL:"+JSON.stringify(' + expression + '));')
        return json.loads(result.rsplit("JEV_FULL:", 1)[1].strip())

    def observe(self):
        """Read a complete current AX observation and the actual app inventory."""
        if not self.application:
            apps = self._json("await cua.listApps({emit:false})")
            applications = [{"id": a["id"], "name": a["displayName"]} for a in apps]
            return describe_window("No application selected yet.", None, applications)
        if self.bound != self.application:
            self.native.js("var jevComputer = await cua.getApp(" + json.dumps(self.application) + ");")
            self.bound = self.application
        # Both reads belong to one observation; avoid a second MCP round trip.
        apps, raw = self._json("[await cua.listApps({emit:false}), await jevComputer.getAXState({emit:false,disableDiffing:true})]")
        applications = [{"id": a["id"], "name": a["displayName"]} for a in apps]
        return describe_window(raw, self.application, applications)

    def execute(self, action):
        """Execute one selected action; never submit as a side effect of filling."""
        kind = action["type"]
        if kind == "switch_app":
            self.application = action["application"]
            return
        if kind == "wait":
            return
        ref = int(action["target"]["id"]) if "target" in action else None
        if kind == "click":
            code = f"await jevComputer.click({ref});"
        elif kind == "scroll":
            code = f"await jevComputer.scroll({ref}, {json.dumps(action['direction'])}, 1);"
        elif kind == "key":
            code = f"await jevComputer.pressKey({json.dumps(action['key'])});"
        elif kind == "replace":
            code = f"await jevComputer.setValue({ref}, {json.dumps(action['text'])});"
        elif kind == "insert":
            # Re-clicking would move the caret and invalidate the selected insertion.
            code = f"await jevComputer.paste({json.dumps(action['text'])});"
        else:
            raise ValueError("Unsupported computer operation: " + kind)
        self.native.js(code)
