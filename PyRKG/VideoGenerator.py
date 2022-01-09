import os
from math import floor
#import numpy, cv2
from subprocess import Popen, PIPE, DEVNULL, STDOUT
from .Controller import Controller
from .Inputs import Inputs
from .CONFIG import *
import pathlib

class VideoGenerator:

    def __init__(self, layout, ghost_file):
        self.controller = Controller()

        self.controller.read_json(layout)
        self.inputs = Inputs()
        self.internal_frame_rate = self.inputs.read_file(ghost_file)

    def run(self, output_filename):
        #video = cv2.VideoWriter(f"demp.{VIDEO_EXTENSION}", cv2.VideoWriter_fourcc(*VIDEO_CODEC), VIDEO_FRAME_RATE, self.controller.size)
        output_filepath = pathlib.Path(output_filename)
        if output_filepath.suffix != VIDEO_EXTENSION:
            raise RuntimeError(f"Expected file extension {VIDEO_EXTENSION}, got filename \"{output_filename}\" with other file extension instead!")

        output_filepath.parent.mkdir(parents=True, exist_ok=True)

        p = Popen(["ffmpeg", "-y", "-f", "image2pipe", "-framerate", str(VIDEO_FRAME_RATE), "-i", "-",
        "-vcodec", "png", "-framerate", str(VIDEO_FRAME_RATE), output_filename],
        stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)

        frame_f = 0.0
        total_frames = self.inputs.get_total_frame_nr()
        while frame_f < total_frames:
            frame = floor(frame_f)
            cur_inputs = self.inputs.get_frame(frame)
            self.controller.process_inputs_and_draw(cur_inputs, TRANSPARENT)
            #video.write(cv2.cvtColor(numpy.array(self.controller.canvas.canvas), cv2.COLOR_RGB2BGR))
            self.controller.canvas.write_to_file(p.stdin, "png")

            percentage = floor(frame * 100 / total_frames)
            print(f"FRAMES WRITTEN : {percentage}% {floor(percentage/5) * '█'}{floor((100-percentage)/5) * '░'}", end="\r")

            frame_f += self.internal_frame_rate / VIDEO_FRAME_RATE

        #video.release()
