import json
import importlib
import os
from .Component import *
from .Canvas import Canvas

class Controller:

    def __init__(self):
        self.size = (100, 100)
        self.bg_colour = (255, 255, 255)

    def read_json(self, layout_name):
        self.components = []

        # parse the json file to a dict
        layout_path = os.path.join("layouts", layout_name)
        with open(os.path.join(layout_path, "config.json")) as f:
            config_text = f.read()
        config = json.loads(config_text)

        # create the canvas
        self.size = (config["width"], config["height"])
        if "bg_color" in config:
            self.bg_colour = tuple(config["bg_color"])
        self.canvas = Canvas(self.size, self.bg_colour, layout_path)

        # create all components
        for comp in config["components"]:
            try:
                comp_class = getattr(importlib.import_module("src.Component"), comp["name"])
            except AttributeError:
                comp_class = getattr(importlib.import_module(f"layouts.{layout_name}.Component"), comp["name"])
            input_type = comp["input_type"] if "input_type" in comp else None
            instance = comp_class(self.canvas, input_type)
            instance.init_component(comp["info"])
            self.components.append((input_type, instance))

    def process_inputs_and_draw(self, inputs, transparent):
        self.canvas.clear_canvas(transparent)
        for input_type, comp in self.components:
            if input_type == "a_btn":
                cur_input = str(inputs[0])
            elif input_type == "b_btn":
                cur_input = str(inputs[1])
            elif input_type == "l_btn":
                cur_input = str(inputs[2])
            elif input_type == "analog":
                cur_input = (inputs[3], inputs[4])
            elif input_type == "trick":
                cur_input = str(inputs[5])
            elif input_type == None:
                cur_input = None

            comp.process_input_and_draw(cur_input)


if __name__ == "__main__":
    c = Controller()
    c.read_json("test")
    c.process_inputs((0, 0, 0, 0, 0, 0))
    c.canvas.show()