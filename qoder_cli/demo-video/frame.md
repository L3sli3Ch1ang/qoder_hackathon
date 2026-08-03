# frame.md — SkillBridge Demo Video Design System

## Palette

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0f172a` | Stage background (slate-900) |
| `--text` | `#f8fafc` | Primary text (slate-50) |
| `--text-dim` | `#94a3b8` | Secondary text (slate-400) |
| `--accent` | `#06b6d4` | Highlights, underlines (cyan-500) |
| `--accent-dim` | `#164e63` | Accent backgrounds (cyan-900) |
| `--success` | `#10b981` | Matched skills (emerald-500) |
| `--warning` | `#f59e0b` | Gap skills (amber-500) |

## Typography

| Element | Size | Weight | Family |
|---|---|---|---|
| h1 (title) | 72px | 700 | Inter, system-ui, sans-serif |
| h2 (scene heading) | 48px | 600 | Inter, system-ui, sans-serif |
| p (body) | 28px | 400 | Inter, system-ui, sans-serif |
| .stat (stats grid) | 56px | 700 | Inter, system-ui, sans-serif |
| .label (badges) | 20px | 500 | Inter, system-ui, sans-serif |

## Timing

| Motion | Duration | Easing |
|---|---|---|
| Fade in | 0.6s | power2.out |
| Slide in (x/y) | 0.5s | power2.out |
| Scale in | 0.4s | back.out(1.2) |
| Stagger (multi-element) | 0.15s per item | — |
| Scene transition gap | 0.3s | — |

## Resolution

- Canvas: 1920 x 1080 (16:9)
- FPS: 30
- Total duration: ~150s (2 min 30 sec)

## Conventions

- All text is left-aligned unless centered on title/close scenes.
- Screenshots use `object-fit: contain` with a subtle drop-shadow.
- Scene headings enter from left (-30px x offset).
- Stats count up or scale in with stagger.
- No background music (text-driven video).
