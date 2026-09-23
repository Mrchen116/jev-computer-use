# Recorded demonstrations

| Demo | Result | Recording |
| --- | --- | --- |
| Tower Defense Clash · CrazyGames | Four waves, full health, three stars | [3:04, original speed](media/tower-defense-clash.mp4) |
| Garden Defenders | Three stars, zero mower use | [2:23, original speed](media/garden-defenders.mp4) |
| Zoho invoice generator | Three items, zero tax, verified USD 440 | [0:59, original speed](media/zoho-invoice.mp4) |

## Tower Defense Clash — commercial game platform

[Watch the full normal-speed recording](media/tower-defense-clash.mp4)

On [CrazyGames](https://www.crazygames.com/game/tower-defense-clash), Jev chooses
complete tower builds from live game state. The outer agent provides the strategy;
the executor handles the chosen clicks and confirmation. The recorded run finishes
all four waves with 500/500 health and three stars, without an intermediate LLM.
The complete recording includes level entry, tutorial, combat and the verdict.

This uses a game-specific Phaser reader and Playwright pointer actions. No visual
recognition, game-clock change or default-native-CUA support is implied. See
[reproduction, timings and failed development runs](../evals/games/clash.md).

## Garden Defenders — custom game adapter

[Watch the full normal-speed recording](media/garden-defenders.mp4)

An existing [third-party game](https://seth-xh.github.io/pvz/), played through an
agent-authored adapter using the [custom Skill workflow](../skills/jev-computer-use/references/adapters.md).
The outer agent prepares observations, complete action choices and priorities;
Jev handles the game loop without an intervening LLM. The game is never paused
for inference. This recording starts before the first action and includes the
victory screen. It was transcoded without changing speed or cutting gameplay.

The final recorded run won the three-wave first level with zero mower use. Two
successive development runs achieved zero mower use; random enemy patterns were
not held fixed, so this is a demonstration, not a controlled success-rate claim.
The first experiment also won but used two mowers. The video shows the final
selection-toggle fix. All results, including the failed initial plant attempt in
the preceding development run, are retained in the [sanitized results](../evals/games/pvz-results.json).

[Reproduction and adapter code](../evals/games/README.md).
This game reads JavaScript state and uses Playwright input; it does not demonstrate
vision or the default native CUA backend. Game artwork belongs to its respective
authors; the project supplies the agent adapter, not the game.

## Zoho invoice generator — real business form

[Watch the full normal-speed recording](media/zoho-invoice.mp4)

On [Zoho's public invoice generator](https://www.zoho.com/invoice/free-invoice-generator.html),
Jev chooses each field and then its prepared literal value. The host supplies the
synthetic invoice and computes the expected total; the worker executes real clicks
and typing. The final run fills 20 fields in 59.50 seconds, with no intermediate
LLM call. All 32 host checks pass: three items, zero tax and USD 440 total.
Nothing is sent or saved online.

This is the custom DOM/Playwright route, not the default native CUA backend.
The uncut recording includes the complete filling run; earlier adapter failures
are retained in the [results and reproduction guide](../evals/forms/zoho.md).
