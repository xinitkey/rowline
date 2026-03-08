from moviepy import VideoFileClip


def mp4_to_mp3(input_path: str, output_path: str) -> None:
    """
    Extract audio from video file and save as MP3.

    Args:
        input_path: Path to input video file (mp4)
        output_path: Path to output audio file (mp3)
    """
    clip = VideoFileClip(input_path)
    audio = clip.audio
    audio.write_audiofile(output_path)
    audio.close()
    clip.close()


if __name__ == "__main__":
    mp4_to_mp3(
        input_path="input.mp4",
        output_path="output.mp3"
    )
