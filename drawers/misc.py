"""Miscellaneous & Free Text/Image Drawer.

Renders RawNotes categorized as 'misc' (free text, notes, or 1-bit images).
"""

from drawers.base import BaseDrawer
from hardware import escpos

# Try importing Pillow for desktop/rich environment image processing
try:
    from PIL import Image
    import io
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class MiscDrawer(BaseDrawer):
    """Drawer for generic text notes and images."""

    def draw(self, note):
        """Yield ESC/POS command byte chunks for free text or bitmap images.

        Args:
            note (core.models.RawNote): RawNote DTO containing text or photo bytes.

        Yields:
            bytes: ESC/POS formatting command chunks.
        """
        # 1. Initialize printer
        yield escpos.INIT

        # 2. Check content type (Binary Photo Data vs Text String)
        if isinstance(note.content, bytes):
            yield from self._draw_image(note)
        else:
            yield from self._draw_text(note)

        # 3. Paper Feed
        yield escpos.feed(4)

    def _draw_text(self, note):
        """Yield ESC/POS bytes for text content."""
        if note.title:
            yield escpos.align("center")
            yield escpos.bold(True)
            yield escpos.text(f"{note.title}\n")
            yield escpos.bold(False)
            yield escpos.reset_mode()
            yield escpos.align("left")
            yield escpos.text("--------------------------------\n")

        if isinstance(note.content, str):
            lines = note.content.split("\n")
            for line in lines:
                yield escpos.text(f"{line}\n")

    def _draw_image(self, note):
        """Yield ESC/POS bytes for image content streaming row-by-row."""
        if note.title:
            yield escpos.align("center")
            yield escpos.bold(True)
            yield escpos.text(f"[Image: {note.title}]\n")
            yield escpos.bold(False)
            yield escpos.align("left")

        # If Pillow is available, decode and resize JPEG/PNG to 384px width dithered bitmap
        if HAS_PIL and isinstance(note.content, bytes):
            try:
                img = Image.open(io.BytesIO(note.content))
                # Calculate height to preserve aspect ratio at 384 dots width
                aspect_ratio = float(img.size[1]) / float(img.size[0])
                target_width = 384
                target_height = int(target_width * aspect_ratio)

                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                img = img.convert("1")  # Convert to 1-bit black/white with dithering

                # Yield image line-by-line (48 bytes per line) to maintain low RAM footprint
                for y in range(target_height):
                    row_pixels = [img.getpixel((x, y)) == 0 for x in range(target_width)]
                    packed_bytes = escpos.pack_pixel_row(row_pixels)
                    yield escpos.raster_image_row(packed_bytes, width_bytes=48)
                    
            except Exception as e:
                yield escpos.text(f"[Image processing error: {e}]\n")
        else:
            # Fallback for raw byte payloads or MicroPython environments without PIL
            yield escpos.text("[Image received: PIL not available for decoding]\n")
