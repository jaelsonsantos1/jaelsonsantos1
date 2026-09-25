from pathlib import Path
from html import escape

from PIL import Image, ImageEnhance, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "duck-source.png"
OUTPUT = ROOT / "assets" / "duck-ascii.svg"

COLS = 54
ROWS = 36
CHAR_W = 7.0
CHAR_H = 11.5
RAMP = " .:-=+*#%@"


def build_ascii() -> list[str]:
    image = Image.open(SOURCE).convert("RGBA")
    alpha = image.getchannel("A")

    rgb = Image.new("RGB", image.size, "white")
    rgb.paste(image.convert("RGB"), mask=alpha)
    gray = ImageOps.grayscale(rgb)
    gray = ImageEnhance.Contrast(gray).enhance(1.35)

    gray = gray.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    alpha = alpha.resize((COLS, ROWS), Image.Resampling.LANCZOS)

    lines: list[str] = []
    for y in range(ROWS):
        chars: list[str] = []
        for x in range(COLS):
            a = alpha.getpixel((x, y)) / 255
            if a < 0.08:
                chars.append(" ")
                continue

            darkness = 1 - (gray.getpixel((x, y)) / 255)
            density = a * (0.28 + 0.72 * darkness)
            index = min(len(RAMP) - 1, max(1, round(density * (len(RAMP) - 1))))
            chars.append(RAMP[index])
        lines.append("".join(chars).rstrip())

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def render_svg(lines: list[str]) -> None:
    width = COLS * CHAR_W + 28
    height = max(1, len(lines)) * CHAR_H + 32
    text = []
    for i, line in enumerate(lines):
        delay = i * 0.035
        y = 21 + i * CHAR_H
        text.append(
            f'<text x="14" y="{y:.1f}" class="row" style="animation-delay:{delay:.3f}s">'
            f'{escape(line)}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-labelledby="title desc">
  <title id="title">ASCII art duck</title>
  <desc id="desc">Animated ASCII rendering of Jaelson's duck mascot</desc>
  <style>
    .row {{
      fill: #3fb950;
      font: 700 10px 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
      white-space: pre;
      opacity: 0;
      animation: reveal .22s ease-out forwards;
    }}
    @keyframes reveal {{
      from {{ opacity: 0; transform: translateX(-4px); }}
      to {{ opacity: 1; transform: translateX(0); }}
    }}
  </style>
  {''.join(text)}
</svg>
'''
    OUTPUT.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    render_svg(build_ascii())
    print(OUTPUT)
