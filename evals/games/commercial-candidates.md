# Commercial demo candidates

Research date: 2026-09-23. The candidate notes below were initially read-only
discovery. Follow-up testing now completed the [Zoho invoice](../forms/zoho.md)
and the [Tower Defense Clash full run](clash.md) with full health. See
[recorded demonstrations](../../docs/demos.md) for selected full runs. Other
candidates remain untested.

## Games

1. **Tower Defense Clash / CrazyGames (first choice)** — https://www.crazygames.com/game/tower-defense-clash
   - Platform describes HTML5, preparation between waves, real-time gold, building/upgrading/spells during combat, 18 replayable levels with star results.
   - Proposed task: finish level one at normal speed, aiming for no leaks; record lives, stars, wall time, decisions. Do not pause for inference.
   - Public NEXT_DATA loader: https://tower-defense-clash.game-files.crazygames.com/tower-defense-clash/1/index.html . Direct static request returned 403; the normally launched iframe exposes current Phaser state, verified in the follow-up. Inspect only via normal platform launch; do not bypass site restrictions.
2. **Endless Siege / CrazyGames** — https://www.crazygames.com/game/endless-siege
   - Platform describes four starter towers, upgrades/selling before and during waves, gradually rising pressure, daily maps.
   - Proposed task: survive first five waves at normal speed; record remaining lives/leaks. A four-minute timeout is an incomplete run, not a win. Record date/map because it changes.
   - Public HTML5 loader: https://endless-siege.game-files.crazygames.com/endless-siege/9/index.html . Static request 403; runtime state unknown.
3. **英雄塔防 / 4399** — https://www.4399.com/flash/252584.htm
   - Platform explicitly says H5/no plugin, tower building and ammunition loading; 82.68 MB.
   - Proposed task: clear first level with timely reloads, normal speed, no paid/advertisement rewards. Duration/results need live check.
   - Page has unilogin=0 (a clue, not confirmation of a login-free live flow). Engine/state access unknown.

Before adapting: normal load without login/payment/install; readable state independently agrees with screen; one real click changes state as expected; normal-speed cycle keeps up. Do not imply HTML5 means an accessible Phaser object. Bloons TD 4 was deprioritized because its platform explicitly reports Ruffle.

## Real business forms

### First choice: Zoho free invoice generator

URL: https://www.zoho.com/invoice/free-invoice-generator.html

Official page exposes actual company/customer inputs, country selects, invoice/date fields, add-line-item, notes, terms, totals and Download/Print. This is a production business utility, not an automation test page. Filling is publicly accessible; do not select Save Online, Save and Send, payment gateway or account signup. Stop at the completed on-page invoice and calculated total; no download is required for the initial demo. Login-free download not live verified.

Proposed synthetic task:
- Sender: Jev Demo Studio; contact Demo Operator; address 100 Example Avenue, Example City; country United States.
- Recipient: Sample Client LLC; address 200 Sample Street, Sample City; country United States.
- Invoice DEMO-20260923; issue 2026-09-23; due 2026-10-23.
- Three rows: Interface review, quantity 2, rate 120; Documentation, quantity 3, rate 40; Demo preparation, quantity 1, rate 80.
- Tax 0, no discount; notes: DEMONSTRATION ONLY - NOT PAYABLE. Terms: Synthetic data for a software demonstration.
- Acceptance: all specified fields and exactly three line items; amounts 240, 120, 80; subtotal and total 440; prominent demonstration note; stop without sending or saving online. Verify dates using the site's actual supported format.

Do not invent unsupported requirements: Zoho FAQ explicitly says its free generator does not support discounts or changing date format. Native accessibility may have unlabeled fields, so inspect first.

### Backup: Invoice-Generator.com

URL: https://invoice-generator.com/
Official help: https://invoice-generator.com/help

Official FAQ explicitly allows free PDF creation/download without signup; real UI includes currency/tax/discount selectors, item quantity/rate and totals. Use the same synthetic three-row task and stop at validated on-page balance 440 with zero tax/discount/shipping. Do not use Send Invoice or payment functions. Help says template values/history are remembered in local storage; use a dedicated temporary browser context to avoid overwriting the user's business data. Do not claim all data stays local merely from local-storage history (PDF generation transport not inspected).

Recording should show the real domain, task description, meaningful field work and final independently checked result. Only the linked follow-up results establish tested demonstrations; the remaining candidates are still research.
