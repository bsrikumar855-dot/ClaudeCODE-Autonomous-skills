# Social preview image specification (1280 × 640)

GitHub shows this image when the repo is linked on social platforms. It is uploaded manually: Settings → General → *Social preview* → Edit → Upload an image. (GitHub recommends at least 640×320 at 2:1; 1280×640 is the recommended size. PNG, JPG or GIF under 1 MB.)

## Delivered asset
- Rendered file: `docs/assets/og-image.png` (1280×640 PNG, ~390 KB), also used as the website's `og:image` and `twitter:image`.
- Source: `site/og-image.html`. To regenerate:
  ```bash
  google-chrome --headless=new --no-sandbox --hide-scrollbars --window-size=1280,640 \
    --screenshot=docs/assets/og-image.png file://$PWD/site/og-image.html
  ```

## Design spec
| Element | Value |
|---|---|
| Canvas | 1280×640, dark navy-to-blue gradient (`#0b1020` → `#10234f` → `#0b5fff`) |
| Safe area | 80 px margins; keep text inside the central ~1000×500 region (platforms crop edges) |
| Logo mark | 84 px rounded square, `#0b5fff`, white "AB" |
| Headline | "AUTO-BUILDER", 84 px bold, white |
| Subhead | "Goal-driven autonomous development skill for Claude Code", 40 px, `#d6e2ff` |
| Chips | `/auto-builder` · `8 subagents` · `Plan · Build · Verify` |
| Footer | repository path and "Apache-2.0", 24 px |
| Contrast | all text ≥ 7:1 against its background |
| Don'ts | No Anthropic/Claude logos or marks, no star counts, no performance claims |

## Alt text
"AUTO-BUILDER: goal-driven autonomous development for Claude Code"
