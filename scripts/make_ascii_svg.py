from pathlib import Path
from html import escape

from PIL import Image, ImageEnhance, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "duck-source.png"
OUTPUT = ROOT / "assets" / "duck-ascii.svg"

COLS = 68
ROWS = 40
RAMP = " .`:-=+*#%@"

SCREEN_X = 56
SCREEN_Y = 42
SCREEN_W = 688
SCREEN_H = 442
TITLEBAR_H = 32
STATUS_H = 30
PAD_X = 24
PAD_Y = 14

CELL_W = (SCREEN_W - PAD_X * 2) / COLS
CELL_H = (SCREEN_H - TITLEBAR_H - STATUS_H - PAD_Y * 2) / ROWS

ROW_DUR = 0.105
STAGGER = 0.105


def build_ascii() -> list[str]:
    image = Image.open(SOURCE).convert("RGBA")
    alpha = image.getchannel("A")

    rgb = Image.new("RGB", image.size, "white")
    rgb.paste(image.convert("RGB"), mask=alpha)
    gray = ImageOps.grayscale(rgb)
    gray = ImageEnhance.Contrast(gray).enhance(1.25)

    gray = gray.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    alpha = alpha.resize((COLS, ROWS), Image.Resampling.LANCZOS)

    lines: list[str] = []
    for y in range(ROWS):
        chars: list[str] = []
        for x in range(COLS):
            a = alpha.getpixel((x, y)) / 255
            if a < 0.07:
                chars.append(" ")
                continue

            lum = gray.getpixel((x, y)) / 255
            darkness = 1 - lum
            density = a * (0.22 + 0.78 * darkness)
            index = min(len(RAMP) - 1, max(1, round(density * (len(RAMP) - 1))))
            chars.append(RAMP[index])
        lines.append("".join(chars))
    return lines


def render_svg(lines: list[str]) -> None:
    canvas_w = 800
    canvas_h = 590
    art_x = SCREEN_X + PAD_X
    art_y = SCREEN_Y + TITLEBAR_H + PAD_Y
    art_w = SCREEN_W - PAD_X * 2
    font_size = CELL_H * 0.92

    parts: list[str] = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" role="img" aria-labelledby="title desc">
  <title id="title">Jaelson's animated ASCII duck in a laptop terminal</title>
  <desc id="desc">A terminal inside a laptop screen types an ASCII duck line by line.</desc>
  <defs>
    <linearGradient id="lid" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#c8ccd1"/>
      <stop offset="1" stop-color="#7d8590"/>
    </linearGradient>
    <linearGradient id="base" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#d8dbe0"/>
      <stop offset="1" stop-color="#8c929b"/>
    </linearGradient>
    <linearGradient id="screen" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#111722"/>
      <stop offset="1" stop-color="#0d1117"/>
    </linearGradient>
  </defs>

  <rect x="28" y="16" width="744" height="500" rx="28" fill="url(#lid)" stroke="#59616b" stroke-width="3"/>
  <rect x="42" y="30" width="716" height="472" rx="18" fill="#080b10"/>
  <circle cx="400" cy="24" r="3.8" fill="#30363d"/>

  <rect x="{SCREEN_X}" y="{SCREEN_Y}" width="{SCREEN_W}" height="{SCREEN_H}" rx="9" fill="url(#screen)" stroke="#30363d"/>
  <line x1="{SCREEN_X}" y1="{SCREEN_Y + TITLEBAR_H}" x2="{SCREEN_X + SCREEN_W}" y2="{SCREEN_Y + TITLEBAR_H}" stroke="#30363d"/>
  <circle cx="{SCREEN_X + 17}" cy="{SCREEN_Y + 16}" r="5" fill="#ff5f56"/>
  <circle cx="{SCREEN_X + 34}" cy="{SCREEN_Y + 16}" r="5" fill="#ffbd2e"/>
  <circle cx="{SCREEN_X + 51}" cy="{SCREEN_Y + 16}" r="5" fill="#27c93f"/>
  <text x="{SCREEN_X + SCREEN_W / 2}" y="{SCREEN_Y + 20}" text-anchor="middle" fill="#7d8590" font-family="SFMono-Regular, Consolas, monospace" font-size="12">jaelson@github: ~$ ./duck.sh</text>
''']

    for row, line in enumerate(lines):
        y_top = art_y + row * CELL_H
        y_text = y_top + CELL_H * 0.78
        delay = row * STAGGER
        safe = escape(line)
        clip_id = f"row-{row}"
        parts.append(
            f'<clipPath id="{clip_id}"><rect x="{art_x:.1f}" y="{y_top:.1f}" width="0" height="{CELL_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{art_w:.1f}" begin="{delay:.3f}s" dur="{ROW_DUR:.3f}s" fill="freeze"/>'
            f'</rect></clipPath>'
        )
        parts.append(
            f'<g clip-path="url(#{clip_id})"><text xml:space="preserve" x="{art_x:.1f}" y="{y_text:.1f}" '
            f'fill="#c9d1d9" font-family="SFMono-Regular, Consolas, monospace" font-size="{font_size:.2f}" '
            f'textLength="{art_w:.1f}" lengthAdjust="spacing">{safe}</text></g>'
        )
        parts.append(
            f'<rect y="{y_top + 1:.1f}" width="{CELL_W:.1f}" height="{max(2, CELL_H - 2):.1f}" fill="#3fb950" opacity="0">'
            f'<animate attributeName="x" from="{art_x:.1f}" to="{art_x + art_w:.1f}" begin="{delay:.3f}s" dur="{ROW_DUR:.3f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.9" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay + ROW_DUR:.3f}s"/>'
            f'</rect>'
        )

    status_line_y = SCREEN_Y + SCREEN_H - STATUS_H
    status_y = status_line_y + 20
    parts.extend([
        f'<line x1="{SCREEN_X}" y1="{status_line_y}" x2="{SCREEN_X + SCREEN_W}" y2="{status_line_y}" stroke="#30363d"/>',
        f'<text x="{SCREEN_X + PAD_X}" y="{status_y}" fill="#7d8590" font-family="SFMono-Regular, Consolas, monospace" font-size="12">jaelson@github:~$ whoami <tspan fill="#c9d1d9">Jaelson Santos</tspan></text>',
        f'<rect x="{SCREEN_X + PAD_X + 233}" y="{status_y - 12}" width="8" height="14" fill="#3fb950"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/></rect>',
        '<path d="M10 520 H790 L752 566 Q748 574 734 574 H66 Q52 574 48 566 Z" fill="url(#base)" stroke="#707781" stroke-width="2"/>',
        '<path d="M337 520 H463 L452 531 Q449 534 440 534 H360 Q351 534 348 531 Z" fill="#aeb4bb"/>',
        '<path d="M48 566 H752" stroke="#5f6670" stroke-width="3" stroke-linecap="round"/>',
        '</svg>'
    ])

    OUTPUT.write_text("".join(parts), encoding="utf-8")


if __name__ == "__main__":
    render_svg(build_ascii())
    print(OUTPUT)
