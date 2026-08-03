# Code Review — Frontend

**Scope:** `templates/base.html`, `templates/index.html`, `templates/partials/results.html`,
`templates/partials/result_card.html`.

## Summary
A server-rendered Jinja UI progressively enhanced with Alpine.js and an HTMX-style `fetch` swap,
styled with Tailwind (CDN) using a token-based design system. The result is a polished, responsive,
dual-theme interface with a clear "transit-line" visual language for the five sectors.

## Strengths
- **Semantic, componentised templates.** `base.html` defines the shell/theme; `results.html` handles
  empty/error/list states; `result_card.html` is a self-contained card included per result. Markup is
  semantic (`<header>`, `<main>`, `<footer>`, `<article>`, `<section>`).
- **Clean fetch/HTMX wiring.** `sendMatch()` posts JSON with `HX-Request: true` and swaps the
  returned partial into `#results`, with a loading skeleton (`#loading`) and a catch-path error banner.
- **Token-based responsive theming.** Every colour resolves to a CSS custom property with a `.dark`
  override; the theme is applied pre-paint (no flash) and persisted to `localStorage` (`sb-theme`).
  Layout is responsive via Tailwind grid (`lg:grid-cols-5`, 40/60 split).
- **Accessibility.** Theme + perspective controls expose `aria-label` / `aria-pressed`; the sector
  strip and decorative glyphs are `aria-hidden`; `[x-cloak]` prevents unstyled flashes; focus rings
  use brand colours.
- **Instant perspective toggle (new).** A shared `Alpine.store('ui', { perspective })` re-frames every
  card client-side (two server-rendered `x-show` banners) with no re-query — matches the demo flow.

## Findings
| # | Severity | File | Finding | Resolution |
|---|----------|------|---------|------------|
| 1 | Low | `base.html`, `index.html` | Tailwind/Alpine/HTMX load from CDNs, so the demo needs network for assets. | Acceptable for a hackathon demo; could vendor for offline. |
| 2 | Low | `index.html` | Empty-input guard uses `alert()`. | Functional; could be an inline error message for polish. |
| 3 | Low | `result_card.html` | The two framing banners are both rendered then toggled, doubling that markup per card. | Negligible at top-10 results; enables instant toggle. |

## Recommendations
- Replace `alert()` with an inline validation message in the input panel.
- Add `aria-live="polite"` to `#results` so screen readers announce result updates.

## Verdict
✅ **Approve.** Semantic templates, responsive token theming, dark mode, accessibility, and the new
instant perspective toggle are all in good shape.
