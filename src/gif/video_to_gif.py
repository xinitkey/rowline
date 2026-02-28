from moviepy import VideoFileClip

def video_to_gif(input_path: str, output_path: str,
                 start: float | None = None,
                 end: float | None = None,
                 fps: int | None = None,
                 width: int | None = None) -> None:
    # загружаем видео
    clip = VideoFileClip(input_path)

    # обрезка по времени (если нужно)
    if start is not None or end is not None:
        clip = clip.subclip(start, end)

    # изменение размера (если нужно)
    if width is not None:
        clip = clip.resize(width=width)

    # сохранение в GIF
    clip.write_gif(output_path, fps=fps)

    clip.close()


if __name__ == "__main__":
    video_to_gif(
        input_path="input.mp4",
        output_path="output.gif",
        start=0,      # сек, можно None
        end=5,        # сек, можно None
        fps=15,       # кадры/сек, можно None (возьмёт из видео)
        width=480     # ширина GIF, можно None (оставит оригинал)
    )
