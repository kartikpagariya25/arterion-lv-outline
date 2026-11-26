# Design system: Arterion LV Outline

A recreation of a clean medical-AI landing page, in sky blue and white. Every claim and number on the page comes from this project's own README and metrics.

## Structure
1. Floating navigation: logo mark, pill tabs, status, sign-in, Get Started
2. Hero: badge, serif headline (italic gradient second line), lead, two calls to action, check-badges, motif line
3. Features: six cards with gradient icon tiles
4. Process: four numbered steps joined by a rail that fills as you scroll
5. Analyze: the working tool
6. Evidence: dark section with an italic claim and a glass panel of held-out metric bars
7. Call to action and footer

## Tokens
| Token | Value |
|---|---|
| `--brand-1` | `#0c4a6e` |
| `--brand-2` | `#0369a1` |
| `--brand-3` | `#0ea5e9` |
| `--bright` | `#7dd3fc` |
| `--ink` | `#0c1a2b` |
| `--muted` | `#5b6f82` |
| `--bg` | `#f6fbfe` |
| `--soft` | `#f0f9ff` |
| `--dark-1` | `#07182b` |
| `--dark-2` | `#0c4a6e` |

## Type
Headlines: 'Lora'. Body: 'Manrope'. Numbers: 'JetBrains Mono'.

## Motion
- **Motion (framer-motion engine, vanilla build):** hero entrance on a spring, button hover and press springs, count-ups.
- **GSAP + ScrollTrigger:** read-progress bar, hero parallax, heading and card reveals, a scrubbed rail that connects the steps, metric bars that grow once in view.
- **Reduced motion:** all animation is skipped and bars and counters show their final values.

## Accessibility
Skip link, labelled landmarks, visible focus rings, text contrast of at least 4.5:1 on buttons, and a keyboard-operable mobile menu.
