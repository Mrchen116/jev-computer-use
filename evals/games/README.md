# Game adapters

- [Tower Defense Clash on CrazyGames](clash.md): commercial platform, full-health
  four-wave win and full normal-speed recording.
- Garden Defenders below: third-party PvZ-style game, zero-mower win.

## Garden Defenders: agent-authored adapter

This experiment follows the Skill's [custom adapter workflow](../../skills/jev-computer-use/references/adapters.md)
on the existing [Garden Defenders game](https://seth-xh.github.io/pvz/)
([upstream source](https://github.com/seth-xh/pvz)). It is a game-specific example,
not a built-in adapter option on `delegate_task` and not a visual game-playing claim.
No game assets or source are bundled here.

The host prepares a small loadout (sunflower, pea, wallnut, cherry), placement zones,
priorities and state/action mappings. Jev chooses complete plant-and-cell actions,
collect or wait. The reader groups live engine objects by row with named types and
shared coordinates; it never changes resources, randomness or the game clock.
Plant macros collect visible sun via the game's C shortcut, then select and click.
The selector checks whether the requested plant is already selected: numeric
shortcuts toggle selection in this game. Every attempt is checked against game state.

The default native CUA runner is unchanged. This prototype uses Playwright CLI in
an isolated browser, real keyboard/pointer input, and the bundled Jev client. There
is no LLM in its per-step loop. Browser command overhead is included in timings;
all setup/iteration LLM costs are outside the game-run measurements.

## Reproduce

Requires Python 3.9+, a working `playwright-cli` (or its Skill wrapper), and a Jev
key file. Open a dedicated headed session; do not reuse personal browser tabs:

```sh
playwright-cli -s=jev-pvz open https://seth-xh.github.io/pvz/ --headed
python3 evals/games/pvz.py --cli /path/to/playwright-cli \
  --key-file /private/jev-key --output /private/pvz-run
```

The output directory must be new. It contains `game.webm` (full normal-speed run),
`progress.json` (compact live status, all concise steps), `history.jsonl` (full private
requests/results), and `summary.json`. Create `STOP` inside it for cooperative stop;
wait for the worker to exit before taking over its browser session. Default limits
are 240 seconds and 150 decisions. The game must remain visible; unexpected pause
or loss of visibility yields instead of silently changing its clock.

Only sanitized result summaries and the selected recording belong in Git. Videos
show an existing third-party game; they do not imply ownership or affiliation.

## Results

See [sanitized development results](pvz-results.json) and the
[full recorded run](../../docs/demos.md). Default-path regression is reported
separately; game success does not establish default UI reliability.

The [default-path regression](default-regression.json) reran three MiniWoB task
types with seed 11 using native CUA and Sol/medium + Jev. All returned official raw
reward 1; 115 core and 22 evaluator tests passed. Wall times were worse than the
historical runs (network retries are retained), so this checks functionality, not
unchanged speed or cost. No native-only baseline was rerun.

[Candidate research and follow-up status](commercial-candidates.md) distinguishes
tested demonstrations from remaining untested games. The [Zoho form demo](../forms/zoho.md)
uses the same custom Skill workflow for sequential interaction.

A final `multi-layouts` seed-11 follow-up after the commercial demos also passed
with official raw reward 1 through native CUA + Sol/medium + Jev. One prior setup
attempt was stopped by the native window-change guard before the agent started;
the fresh attempt passed. The same 137 offline tests passed. Details are in
[the regression record](default-regression.json).
