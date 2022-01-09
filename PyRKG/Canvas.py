from PIL import Image, ImageFont, ImageDraw
import os
from .CONFIG import TRANSPARENT

class Canvas:

    def __init__(self, dimension, bg_colour, layout_path):
        self.dimension = dimension
        self.canvas = Image.new("RGBA", self.dimension)
        self.draw_ctx = ImageDraw.Draw(self.canvas)
        self.bg_colour = bg_colour
        self.layout_path = layout_path
        self.images = dict()
        self.fonts = dict()

    def clear_canvas(self, transparency=False):
        self.canvas = Image.new("RGBA", self.dimension)
        if transparency and TRANSPARENT:
            bg_colour = (0, 0, 0, 0)
        else:
            bg_colour = (self.bg_colour[0], self.bg_colour[1], self.bg_colour[2])
        self.canvas.paste(bg_colour, (0, 0, self.canvas.size[0], self.canvas.size[1]))
        self.draw_ctx = ImageDraw.Draw(self.canvas)

    def load_image(self, file_path):
        if file_path not in self.images:
            self.images[file_path] = Image.open(os.path.join(self.layout_path, file_path))

    def draw_image(self, file_path, position):
        self.canvas.paste(self.get_image(file_path), position, self.get_image(file_path))

    def get_image(self, file_path):
        return self.images[file_path]

    def load_font(self, font_path, size):
        key = (font_path, size)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(os.path.join(self.layout_path, font_path), size)

    def draw_text(self, text, **kwargs):
        try:
            kwargs["fill"] = tuple(kwargs["fill"])
        except KeyError:
            pass
        try:
            kwargs["stroke_fill"] = tuple(kwargs["stroke_fill"])
        except KeyError:
            pass

        # pop "font", "size" and "position" from kwargs as they are already handled by Canvas
        self.draw_ctx.text(kwargs.pop("position"), text, font=self.fonts[(kwargs.pop("font"), kwargs.pop("size"))], **kwargs)

    def show(self):
        self.canvas.show()

    def write_to_file(self, path, format):
        self.canvas.save(path, format)


if __name__ == "__main__":
    canvas = Canvas((500, 500), (150, 100, 200))
    canvas.load_image("bert_the_pencil.png")
    canvas.set_sprite("bert_the_pencil.png", position=(50, 50))
    canvas.draw()
