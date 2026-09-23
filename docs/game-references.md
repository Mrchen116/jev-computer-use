# What the game demonstrations establish

Reviewed 2026-09-21. These are source observations, not reproduced upstream scores.

- [shantanugoel/mario-jev](https://github.com/shantanugoel/mario-jev)
  explicitly pauses the emulator while awaiting a decision. Its input is decoded
  RAM, with separate movement and jump questions. Finishing a level in this mode
  does not establish wall-clock reaction performance.
- [fhshaik/typesafe-mario](https://github.com/fhshaik/typesafe-mario/blob/main/src/typesafe_mario/runner.py)
  has a dashboard loop that advances the emulator while one policy request runs
  in a background thread. It continues the previous controller action until a new
  result arrives. Structured telemetry and game-specific action macros are part
  of its controller. Its stepwise modes have different timing semantics.
- [TypeSafe's introduction](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
  describes typed decisions over program state. Its Doom demonstration uses
  structured state, not images; its published latency measurements are largely
  from the US West Coast, where the service was based at launch.

Our input is the ordinary native accessibility tree and visible control menu.
We have no game RAM, physics parser or privileged game API in the agent. We
therefore test the actual browser/control/network loop, not provider inference
latency alone. A typed output prevents an out-of-schema choice; it does not
establish that the chosen action is correct or timely.

The original Semantic Sprint waited indefinitely for an answer. It was useful
for measuring semantic click cost, but could not test real-time failure. It is
retained only as development evidence. Rescue Dispatch adds a server-clock
four-second deadline, automatic expiration, rejected stale clicks, and a 10/12
winning score. The animation and accessible text represent the same live task.
These rules are fixed before paired validation, and normal native batching is
allowed in both arms. The evaluation must report the result even if an LLM
constructs a successful fast strategy.

This remains a small accessible semantic game, not a reproduction of Mario,
Plants vs. Zombies, or a pixel-based general game-playing benchmark. See the
[experiment protocol](../evals/computer_use/PROTOCOL.md) for the complete boundary.
