from moviepy import VideoFileClip


def video_to_gif(input_path: str, output_path: str,
                 start: float | None = None,
                 end: float | None = None,
                 fps: int | None = None,
                 width: int | None = None) -> None:
    clip = VideoFileClip(input_path)
    if start is not None or end is not None:
        clip = clip.subclip(start, end)
    if width is not None:
        clip = clip.resize(width=width)
    clip.write_gif(output_path, fps=fps)
    clip.close()
