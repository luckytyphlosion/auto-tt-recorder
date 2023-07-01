import os
import PyRKG.VideoGenerator

def main():
    video_generator = PyRKG.VideoGenerator.VideoGenerator("nunchuck", "02m16s3252553 Lυkε.rkg")
    print("Generating input display!")
    video_generator.run(f"temp/input_display_nunchuck.mov", "ffmpeg")


if __name__ == "__main__":
    main()
