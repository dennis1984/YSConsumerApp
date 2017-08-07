from barcode import writer
from barcode.writer import ImageFont, FONT, mm2px


class ImageWriter(writer.ImageWriter):
    def __init__(self):
        super(ImageWriter, self).__init__()

    def _paint_text(self, xpos, ypos):
        font = ImageFont.truetype(FONT, self.font_size * 3)
        width, height = font.getsize(self.text)
        pos = (mm2px(xpos, self.dpi) - width // 3,
               mm2px(ypos, self.dpi) - height // 4)
        self._draw.text(pos, self.text, font=font, fill=self.foreground)
