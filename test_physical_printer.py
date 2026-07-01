import time
from machine import UART
from hardware import escpos

def test_printer():
    # Initialize UART (adjust TX/RX to match your wiring)
    # Swapped: TX=17, RX=18
    print("Initializing UART...")
    uart = UART(1, baudrate=9600, tx=18, rx=17)
    time.sleep(0.5)  # Let UART stabilize
    
    print("Sending test sequences...")
    
    # 1. Initialize printer
    uart.write(escpos.INIT)
    
    # 2. Text & Line feed
    uart.write(escpos.text("--- ESC/POS Command Test ---\n"))
    uart.write(escpos.LF)
    
    # 3. Alignment
    uart.write(escpos.align("left") + escpos.text("Left Aligned\n"))
    uart.write(escpos.align("center") + escpos.text("Center Aligned\n"))
    uart.write(escpos.align("right") + escpos.text("Right Aligned\n"))
    uart.write(escpos.align("left"))  # Reset to left
    
    # 4. Text styles
    uart.write(escpos.bold(True) + escpos.text("Bold Text\n") + escpos.bold(False))
    uart.write(escpos.underline(True, 1) + escpos.text("Underline 1-dot\n"))
    uart.write(escpos.underline(True, 2) + escpos.text("Underline 2-dot\n") + escpos.underline(False))
    uart.write(escpos.reverse_colors(True) + escpos.text(" Reverse Colors \n") + escpos.reverse_colors(False))
    
    # 5. Font sizing
    uart.write(escpos.font_size(2, 2) + escpos.text("Double Size\n") + escpos.font_size(1, 1))
    
    # 6. Line spacing
    uart.write(escpos.line_spacing(15) + escpos.text("Tight line spacing line 1\nTight line spacing line 2\n"))
    uart.write(escpos.line_spacing(None))  # Reset to default
    
    # 7. Raster graphics streaming (384 dots / 8 = 48 bytes)
    uart.write(escpos.text("Testing 1-bit raster graphics:\n"))
    for r in range(24):
        # Checkerboard pattern generator
        pixels = [((r // 4) + (c // 8)) % 2 == 0 for c in range(384)]
        row_bytes = escpos.pack_pixel_row(pixels)
        uart.write(escpos.raster_image_row(row_bytes, width_bytes=48))
        
    # 8. Paper feed
    uart.write(escpos.feed(4))
    print("Test run completed.")

if __name__ == "__main__":
    test_printer()
