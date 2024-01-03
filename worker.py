import subprocess
from openai import OpenAI
import os

# Set OpenAI Key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def convert_ogg_to_mp3(ogg_file_path, mp3_file_path, overwrite=True):
    command = [
        'ffmpeg',
        '-y' if overwrite else '-n',  # Overwrite file if it exists (-y) or do not overwrite (-n)
        '-i', ogg_file_path,  # Input file
        '-codec:a', 'libmp3lame',  # Use mp3 codec
        '-q:a', '2',  # Set the quality of the mp3
        mp3_file_path  # Output file
    ]

    subprocess.run(command, check=True)


def transcribe(file_name_mp3):
    audio_file = open(f"audio/{file_name_mp3}", "rb")

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

    result = transcript.text
    return result


def summarize(transcript):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": f"""
                    Translate the following text into English as briefly as possible in bullet points in German. Pay very close attention to the number of words you use. Never exceed 93 words. Use fewer words if possible. Be precise and focus on the essential information. Write from the perspective as if you were the author of the message: {transcript}
                """,
            },
        ]
        ,
        max_tokens=500,
    )
    response_text = response.choices[0].message.content
    if response_text == "I'm sorry":
        return None
    else:
        return response_text
