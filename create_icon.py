"""
create_icon.py — Generate desktop/zhub.ico for the PyInstaller build.

Run ONCE before building:
    python create_icon.py

Requires: Pillow (pip install pillow  — already in requirements.txt).
Output:   desktop/zhub.ico  (multi-resolution: 16, 32, 48, 64, 128, 256 px)
"""
import os
from PIL import Image, ImageDraw

# Icon sizes required for a well-formed Windows .ico file
SIZES = [16, 32, 48, 64, 128, 256]

# Bootstrap primary blue (#0d6efd) — matches the ZHub navbar
BG_COLOR   = (13, 110, 253, 255)
TEXT_COLOR = (255, 255, 255, 255)


def _draw_frame(size):
    """
    Create a single square RGBA image of `size` x `size` pixels containing:
      - A blue rounded-rectangle background.
      - A white Z drawn with three bold lines (no system font required).
    """
    img  = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Background rounded rectangle ──────────────────────────────────────
    margin = max(1, size // 8)
    radius = max(2, size // 5)
    draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=radius,
        fill=BG_COLOR,
    )

    # ── Letter Z drawn with three lines ───────────────────────────────────
    # Padding inside the blue rectangle
    pad   = max(2, size // 4)
    thick = max(2, size // 9)

    # Vertical thirds of the blue area define top and bottom of the Z
    inner_top = margin + (size - 2 * margin) // 4
    inner_bot = margin + 3 * (size - 2 * margin) // 4

    left  = pad
    right = size - pad

    # Top horizontal bar: left → right at inner_top
    draw.line([(left, inner_top), (right, inner_top)],
              fill=TEXT_COLOR, width=thick)

    # Diagonal stroke: top-right → bottom-left
    draw.line([(right, inner_top), (left, inner_bot)],
              fill=TEXT_COLOR, width=thick)

    # Bottom horizontal bar: left → right at inner_bot
    draw.line([(left, inner_bot), (right, inner_bot)],
              fill=TEXT_COLOR, width=thick)

    return img


def main():
    os.makedirs('desktop', exist_ok=True)

    frames = [_draw_frame(s) for s in SIZES]

    output_path = os.path.join('desktop', 'zhub.ico')
    frames[0].save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:],
    )
    print(f'Icon created successfully: {output_path}')
    print(f'Sizes included: {SIZES}')


if __name__ == '__main__':
    main()
