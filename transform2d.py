import ffmpeg

class Rectangle:
    __slots__ = ("name", "original_x", "original_y", "original_width", "original_height", "final_x", "final_y", "final_width", "final_height", "children")

    def __init__(self, name, x, y, width, height):
        self.name = name
        self.original_x = x
        self.original_y = y
        self.original_width = width
        self.original_height = height
        self.final_x = x
        self.final_y = y
        self.final_width = width
        self.final_height = height
        self.children = []

    def add_child_relative_to(self, name, x_offset, y_offset, width, height):
        child_rect = Rectangle(name, self.final_x + x_offset, self.final_y + y_offset, width, height)
        #child_rect = Rectangle(name, x_offset, y_offset, width, height)
        self.children.append(child_rect)
        return child_rect

    def scale(self, multiplier):
        self.final_x *= multiplier
        self.final_y *= multiplier
        self.final_width *= multiplier
        self.final_height *= multiplier
        for child in self.children:
            child.scale(multiplier)

    def scale_manual_dimensions(self, multiplier, width, height):
        self.final_x *= multiplier
        self.final_y *= multiplier
        self.final_width = width
        self.final_height = height
        for child in self.children:
            child.scale(multiplier)

# inputs_width=1216
# inputs_height=769
# inputs_x=148
# inputs_y=2161
# box_x=209
# box_y=2195
# box_width=1060
# box_height=681

BASE_INPUTS_WIDTH = 1216
BASE_INPUTS_HEIGHT = 769
BASE_INPUTS_X = 148
BASE_INPUTS_Y = 2161
BASE_INPUT_BOX_X = 209
BASE_INPUT_BOX_Y = 2195
BASE_INPUT_BOX_WIDTH = 1060
BASE_INPUT_BOX_HEIGHT = 681

base_framedump_dimensions = {
    "2160p": (5793, 3168),
    "1440p": (3862, 2112),
    "1080p": (2897, 1584),
    "720p": (1931, 1056),
    "480p": (966, 528)
}

framedump_scale_factors_from_2160p = {
    "2160p": 1,
    "1440p": 2/3,
    "1080p": 1/2,
    "720p": 1/3,
    "480p": 1/6
}

# 4k canvas dimensions: 5793x3168

class FFmpegInStreamInfo:
    __slots__ = ("name", "stream", "start_frame", "end_frame", "before_setpts", "after_setpts", "eof_action", "scale_flags")

    def __init__(self, name, stream, start_frame=None, end_frame=None, before_setpts=None, after_setpts=None, eof_action="repeat", scale_flags="bicubic"):
        self.name = name
        self.stream = stream
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.before_setpts = before_setpts
        self.after_setpts = after_setpts
        self.eof_action = eof_action
        self.scale_flags = scale_flags

FPS = 59.94005994006

def apply_ffmpeg_filters(canvas, ffmpeg_in_streams_info):
    apply_ffmpeg_scale_filters(canvas, ffmpeg_in_streams_info, do_not_scale=True)

    return apply_ffmpeg_overlay_filters(canvas, ffmpeg_in_streams_info)

def apply_ffmpeg_scale_filters(rect, ffmpeg_in_streams_info, do_not_scale=False):

    rect_stream_info = ffmpeg_in_streams_info[rect.name]

    if not do_not_scale:
        rect_stream_info.stream = ffmpeg.filter(rect_stream_info.stream, "scale", rect.final_width, rect.final_height, flags=rect_stream_info.scale_flags)

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

    #print(f"canvas_stream: {canvas_stream}")

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

def calc_overlay_objs_coords_dimensions(dolphin_resolution, output_width, ffmpeg_in_streams_info):
    canvas_width_2160p, canvas_height_2160p = base_framedump_dimensions["2160p"]
    canvas = Rectangle("canvas", 0, 0, canvas_width_2160p, canvas_height_2160p)
    input_box = canvas.add_child_relative_to("input_box", BASE_INPUT_BOX_X, BASE_INPUT_BOX_Y, BASE_INPUT_BOX_WIDTH, BASE_INPUT_BOX_HEIGHT)
    inputs = input_box.add_child_relative_to("inputs", BASE_INPUTS_X - BASE_INPUT_BOX_X, BASE_INPUTS_Y - BASE_INPUT_BOX_Y, BASE_INPUTS_WIDTH, BASE_INPUTS_HEIGHT)

    #if output_width is not None:
    #    canvas.scale(output_width / canvas_width_2160p)
    #else:
    canvas_width, canvas_height = base_framedump_dimensions[dolphin_resolution]
    canvas.scale_manual_dimensions(framedump_scale_factors_from_2160p[dolphin_resolution], canvas_width, canvas_height)
    #canvas.scale(framedump_scale_factors_from_2160p[dolphin_resolution])

    final_base_stream = apply_ffmpeg_filters(canvas, ffmpeg_in_streams_info)

    return final_base_stream
