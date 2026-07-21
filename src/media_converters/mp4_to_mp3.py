from moviepy import VideoFileClip


def mp4_to_mp3(input_path: str, output_path: str) -> None:
    clip = VideoFileClip(input_path)
    audio = clip.audio
    audio.write_audiofile(output_path)
    audio.close()
    clip.close()
