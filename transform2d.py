import ffmpeg
from constants.encode import *

class Rectangle:
    __slots__ = ("name", "x_offset", "y_offset", "width", "height", "final_x", "final_y", "final_width", "final_height", "vertical_stretch_factor", "children", "scale_factor", "final_width_override", "final_height_override", "parent")

    def __init__(self, name, x_offset, y_offset, width, height, parent=None, scale_factor=1, vertical_stretch_factor=1, final_width_override=None, final_height_override=None):
        self.name = name

        self.x_offset = x_offset
        self.y_offset = y_offset
        self.width = width
        self.height = height

        self.final_x = x_offset
        self.final_y = y_offset
        self.final_width = width
        self.final_height = height

        self.parent = parent

        self.scale_factor = 1
        self.vertical_stretch_factor = 1
        self.final_width_override = final_width_override
        self.final_height_override = final_height_override

        self.children = []

    def add_child_relative_to(self, name, x_offset, y_offset, width, height):
        child_rect = Rectangle(name, x_offset, y_offset, width, height, parent=self)
        self.children.append(child_rect)
        return child_rect

    def stretch_vertical(self, multiplier):
        self.vertical_stretch_factor = multiplier

    def scale(self, scale_factor):
        self.scale_factor = scale_factor

        for child in self.children:
            child.scale(scale_factor)

    def scale_manual_dimensions(self, scale_factor, width, height):
        self.scale_factor = scale_factor
        self.final_width_override = width
        self.final_height_override = height

        for child in self.children:
            child.scale(scale_factor)

    def calculate_final_dimensions(self):
        if self.final_width_override is not None:
            self.width = self.final_width_override
        elif self.scale_factor != 1:
            self.width = self.width * self.scale_factor

        if self.final_height_override is not None:
            self.height = self.final_height_override
        elif self.scale_factor != 1:
            self.height = self.height * self.scale_factor

        if self.vertical_stretch_factor != 1:
            self.height = self.height * self.vertical_stretch_factor
            for child in self.children:
                child_old_y_offset = child.y_offset
                child.y_offset *= self.vertical_stretch_factor
                child.y_offset += (child.height * (self.vertical_stretch_factor - 1))/2

        if self.scale_factor != 1:
            if self.parent is None:
                self.x_offset = self.x_offset * self.scale_factor
                self.y_offset = self.y_offset * self.scale_factor
            else:
                self.x_offset = self.parent.x_offset + self.x_offset * self.scale_factor
                self.y_offset = self.parent.y_offset + self.y_offset * self.scale_factor

        self.final_x = self.x_offset
        self.final_y = self.y_offset
        self.final_height = self.height
        self.final_width = self.width

        for child in self.children:
            child.calculate_final_dimensions()

# 4k canvas dimensions: 5793x3168

class FFmpegInStreamInfo:
    __slots__ = ("name", "stream", "start_frame", "end_frame", "before_setpts", "after_setpts", "eof_action", "scale_flags", "apply_stretch")

    def __init__(self, name, stream, start_frame=None, end_frame=None, before_setpts=None, after_setpts=None, eof_action="repeat", scale_flags="bicubic", apply_stretch=False):
        self.name = name
        self.stream = stream
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.before_setpts = before_setpts
        self.after_setpts = after_setpts
        self.eof_action = eof_action
        self.scale_flags = scale_flags
        self.apply_stretch = apply_stretch

FPS = 59.94005994006

def apply_ffmpeg_filters(canvas, ffmpeg_in_streams_info):
    apply_ffmpeg_scale_filters(canvas, ffmpeg_in_streams_info, is_canvas=True)

    return apply_ffmpeg_overlay_filters(canvas, ffmpeg_in_streams_info)

def apply_ffmpeg_scale_filters(rect, ffmpeg_in_streams_info, is_canvas=False):

    rect_stream_info = ffmpeg_in_streams_info[rect.name]

    if not is_canvas or (rect.vertical_stretch_factor != 1):
        rect_stream_info.stream = ffmpeg.filter(rect_stream_info.stream, "scale", round(rect.final_width), round(rect.final_height), flags=rect_stream_info.scale_flags)
        if is_canvas:
            rect_stream_info.stream = ffmpeg.filter(rect_stream_info.stream, "setsar", 1, 1)

    for child in rect.children:
        apply_ffmpeg_scale_filters(child, ffmpeg_in_streams_info)

def apply_ffmpeg_overlay_filters(canvas, ffmpeg_in_streams_info):
    canvas_stream = ffmpeg_in_streams_info["canvas"].stream
    return apply_ffmpeg_overlay_filters_helper(canvas_stream, canvas, ffmpeg_in_streams_info, do_not_overlay=True)

def apply_ffmpeg_overlay_filters_helper(canvas_stream, rect, ffmpeg_in_streams_info, do_not_overlay=False):
    if not do_not_overlay:
        canvas_stream = overlay_onto_canvas(canvas_stream, rect, ffmpeg_in_streams_info)

    for child in rect.children:
        canvas_stream = apply_ffmpeg_overlay_filters_helper(canvas_stream, child, ffmpeg_in_streams_info)

    return canvas_stream

def overlay_onto_canvas(canvas_stream, rect, ffmpeg_in_streams_info):
    stream_info = ffmpeg_in_streams_info[rect.name]
    rect_stream = stream_info.stream

    if stream_info.before_setpts is not None:
        rect_stream = rect_stream.setpts(stream_info.before_setpts)

    if stream_info.start_frame is not None:
        rect_on_canvas = ffmpeg.filter(
            (canvas_stream, rect_stream),
            "overlay",
            enable=f"between(t,{stream_info.start_frame/FPS},{stream_info.end_frame/FPS})",
            x=rect.final_x,
            y=rect.final_y,
            eof_action=stream_info.eof_action,
            eval="init",
        )
    else:
        rect_on_canvas = ffmpeg.filter(
            (canvas_stream, rect_stream),
            "overlay",
            x=rect.final_x,
            y=rect.final_y,
            eof_action=stream_info.eof_action,
            eval="init"
        )

    if stream_info.after_setpts is not None:
        rect_on_canvas = rect_on_canvas.setpts(stream_info.after_setpts)

    return rect_on_canvas

def calc_overlay_objs_coords_dimensions(dolphin_resolution, input_display, aspect_ratio_16_by_9, ffmpeg_in_streams_info):
    input_display_geometry = input_display.geometry
    canvas_width_2160p, canvas_height_2160p = base_framedump_dimensions["2160p"]
    canvas = Rectangle("canvas", 0, 0, canvas_width_2160p, canvas_height_2160p)

    input_box = canvas.add_child_relative_to("input_box", input_display_geometry.base_input_box_x, input_display_geometry.base_input_box_y, input_display_geometry.base_input_box_width, input_display_geometry.base_input_box_height)
    inputs = input_box.add_child_relative_to("inputs", input_display_geometry.base_inputs_x - input_display_geometry.base_input_box_x, input_display_geometry.base_inputs_y - input_display_geometry.base_input_box_y, input_display_geometry.base_inputs_width, input_display_geometry.base_inputs_height)

    canvas_width, canvas_height = base_framedump_dimensions[dolphin_resolution]

    if aspect_ratio_16_by_9:
        vertical_stretch_factor = (canvas_width*9)/(canvas_height*16)
    else:
        vertical_stretch_factor = 1

    canvas.scale_manual_dimensions(framedump_scale_factors_from_2160p[dolphin_resolution], canvas_width, canvas_height)
    canvas.stretch_vertical(vertical_stretch_factor)

    canvas.calculate_final_dimensions()

    final_base_stream = apply_ffmpeg_filters(canvas, ffmpeg_in_streams_info)

    return final_base_stream
