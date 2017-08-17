from barcode import writer
from barcode.writer import ImageFont, BaseWriter


class ImageWriter(writer.ImageWriter):
    def _paint_text(self, xpos, ypos):
        return None
        # font = ImageFont.truetype(FONT, self.font_size * 3)
        # width, height = font.getsize(self.text)
        # pos = (mm2px(xpos, self.dpi) - width // 3,
        #        mm2px(ypos, self.dpi) - height)
        # self._draw.text(pos, self.text, font=font, fill=self.foreground)
