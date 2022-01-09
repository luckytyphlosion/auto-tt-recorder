from math import floor

class Component:

    supported_input_types = ["a_btn", "b_btn", "l_btn", "analog", "trick"]

    def __init__(self, canvas, input_type: str):
        self.canvas = canvas
        if input_type is not None and input_type not in self.supported_input_types:
            raise Exception(f'"{input_type}" is not supported by {self.__class__.__name__}')
        else:
            self.input_type = input_type

    def init_component(self, info: dict):
        pass

    def process_input_and_draw(self, current_input):
        pass


class Categorical_C(Component):

    supported_input_types = ["a_btn", "b_btn", "l_btn", "trick"]
    info_format = {
        "categories": {
            str: { # string representing category
                "position": [int, int], # [x, y]
                "image": str # image file name
            }
        }
    }

    def init_component(self, info: dict):
        self.categories = info["categories"]
        for category in self.categories.values():
            self.canvas.load_image(category["image"])

    def process_input_and_draw(self, current_input):
        cur_info = self.categories[current_input]
        if cur_info["image"] is not None:
            self.canvas.draw_image(cur_info["image"], cur_info["position"])


class Tuple_C(Component):

    supported_input_types = ["analog"]
    info_format = {
        "image": str, # image file name
        "position": list, # [x, y]
        "pos_range": list # [x, y] x and y specify how far the image can move from its position in the x and y range respectively
    }

    def init_component(self, info: dict):
        self.image = info["image"]
        self.pos_range = tuple(info["pos_range"])
        self.position = tuple(info["position"])
        
        self.canvas.load_image(self.image)

    def process_input_and_draw(self, current_input):
        delta_pos = (floor((current_input[1] - 7) * self.pos_range[0] / 7), floor((7 - current_input[0]) * self.pos_range[1] / 7))
        cur_position = (self.position[0] + delta_pos[0], self.position[1] + delta_pos[1])
        self.canvas.draw_image(self.image, cur_position)


class Text_C(Component):

    supported_input_types = ["a_btn", "b_btn", "l_btn", "analog", "trick"]
    info_format = {
        "position": list, # [x, y]
        "font": str, # font file name
        "size": int, # font size
        
        # The following are all optional, they are all directly taken from Pillow's text function 
        # https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.text

        "fill": [int, int, int], # text colour
        "spacing": int, # if multiline text, the number of pixels between the lines
        "align": str, # if multiline text, "left", "center" or "right"
        "direction": str, # if multiline text, "rtl" (right to left), "ltr" (left to right) or "ttb" (top to bottom)
        "stroke_width": int, # text stroke width, also known as text border
        "stroke_fill": [int, int, int] # text stroke colour
    }

    def init_component(self, info: dict):
        self.info = info
        self.position = tuple(info["position"])
        self.canvas.load_font(self.info["font"], self.info["size"])

    def process_input_and_draw(self, current_input):
        if self.input_type == "a_btn":
            text = f"A: {current_input}"
        elif self.input_type == "b_btn":
            text = f"B: {current_input}"
        elif self.input_type == "l_btn":
            text = f"L: {current_input}"
        elif self.input_type == "analog":
            text = f"{str(current_input)}"
        elif self.input_type == "trick":
            text = f"TRICK: {current_input}"
        
        self.canvas.draw_text(text, **self.info)


class StaticImage_C(Component):

    info_format = {
        "image": str, # image file name
        "position": list # [x, y]
    }

    def init_component(self, info: dict):
        self.image = info["image"]
        self.position = tuple(info["position"])
        self.canvas.load_image(self.image)

    def process_input_and_draw(self, current_input):
        self.canvas.draw_image(self.image, self.position)
