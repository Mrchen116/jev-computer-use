# Tower Defense Clash on CrazyGames

[Game](https://www.crazygames.com/game/tower-defense-clash) ·
[Full recording](../../docs/media/tower-defense-clash.mp4) ·
[All development results](clash-results.json)

The recorded first level wins all four waves with **500/500 health and three
stars**. Jev makes 55 decisions, builds seven towers, and needs no intermediate
LLM intervention. Ten non-wait operations succeed; the remainder wait while
defenses fight. The uncut, normal-speed video lasts 183.52 seconds at 25 fps.
Jev response averages 0.41 seconds; a complete cycle averages 3.19 seconds,
including state reads and verification. The requested two-second minimum cycle
is not a guarantee. No pause or fast-forward is used for inference.

The outer agent supplies an aggressive early-defense strategy. Jev chooses tower
type, position and timing from affordable complete actions. The executor opens
the chosen site, selects the chosen tower and confirms, then verifies the tower
count. It never silently substitutes a tower or chooses the next defense.
Tutorial choices follow the currently displayed instruction. Game state is read
from the normally loaded Phaser iframe; all mutations use real pointer input.

This follows the Skill's custom observation/action route. It is a specific adapter,
not universal Canvas perception and not the default native CUA backend. The host
still needs to inspect each game's state and controls. No game assets are bundled.

## Reproduce

Use an installed Playwright CLI, Python 3.9+, and a private Jev key. Open a dedicated
headed session and use normal UI controls to reach the level map. Choose English
for this example. Reload before replay: this game's in-game restart can retain a
destroyed tutorial target. Complete platform guest/language prompts normally.

```sh
playwright-cli -s=jev-clash open https://www.crazygames.com/game/tower-defense-clash --headed
# Inspect the map and identify the level-one marker's center in game coordinates.
python3 evals/games/clash.py --cli /path/to/installed/playwright-cli \
  --session jev-clash --key-file /private/jev-key \
  --output /private/new-clash-run --start-point 87 312
```

The recorded map used a 900×480 game coordinate system. Recheck the marker after
site updates; the executor scales to the actual canvas. Omit `--start-point` only
if the game is already at the beginning of the level. Recording starts before the
optional setup click. The script yields on errors, repeated failed actions, help,
completion, unexpected pause, host `STOP` file, or its time/step budget.

Outputs are `game.webm`, full private `history.jsonl`, compact `progress.json`
including every concise outcome, and `summary.json` with current state and the
browser session for takeover. Wait for exit before operating that session.

## What changed during the experiment

- Observe the actual phase and current objects; a main menu or destroyed replay
  object is not a ready level.
- Let frame-polled controls register pointer hover/press and finish transitions.
  Treat opening, selecting and confirming a chosen build as one mechanical action.
- Align option wording with strategy. Permissive “preserve resources” waiting
  produced one tower and lost health; explicit early construction produced a win.
- Reuse the installed CLI instead of resolving an npm package on every cycle.

Earlier losses, setup errors and interrupted runs remain in the results. A prior
calibration also won at full health, but started midway through the tutorial and
is not the showcased video. These are development runs, not a success-rate study.
Outer-agent research, setup and iteration costs are outside the recorded loop.
