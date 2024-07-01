from flask import Blueprint, request, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import cv2
from moviepy.editor import VideoFileClip
import time
import base64
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

video_bp = Blueprint('video', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_video(video_path, seconds_per_frame=2):
     base64Frames = []
     base_video_path, _ = os.path.splitext(video_path)

     video = cv2.VideoCapture(video_path)
     total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
     fps = video.get(cv2.CAP_PROP_FPS)
     frames_to_skip = int(fps * seconds_per_frame)
     curr_frame=0

     # Loop through the video and extract frames at specified sampling rate
     while curr_frame < total_frames - 1:
         video.set(cv2.CAP_PROP_POS_FRAMES, curr_frame)
         success, frame = video.read()
         if not success:
             break
         _, buffer = cv2.imencode(".jpg", frame)
         base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
         curr_frame += frames_to_skip
     video.release()

     # Extract audio from video
     audio_path = f"{base_video_path}.mp3"
     clip = VideoFileClip(video_path)
     clip.audio.write_audiofile(audio_path, bitrate="32k")
     clip.audio.close()
     clip.close()

     print(f"Extracted {len(base64Frames)} frames")
     print(f"Extracted audio to {audio_path}")
     return base64Frames, audio_path


@video_bp.route('/summarize', methods=['POST'])
def summarize_video():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join('./data/videos', filename)
        file.save(filepath)

        # DO the video
        base64Frames, audio_path = process_video(filepath, seconds_per_frame=10)

        session['past'].append(f"Video: {filename}")

        session['prompts'].append({"role": "system", "content": "Always return the answer in HTML format."})
        messages=[
            {"role": "system", "content": "You are a helpful assistant that can summarise video. Respond in HTML"},
            {"role": "user", "content": ["These are the frames from the video.",
                *map(lambda x: {"type": "image_url",
                "image_url": {"url": f'data:image/jpg;base64,{x}', "detail": "low"}}, base64Frames)
            ]}
         ]

        response = client.chat.completions.create(model="gpt-4o", messages=messages)
        message_content = response.choices[0].message.content
        session['past'].append(filepath)
        session['generated'].append(message_content)
        session['prompts'].append({"role": "assistant", "content": message_content})

        # now do the AUDIO
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(audio_path, "rb"),
        )
        messages=[
            {"role": "system", "content":"""You are generating a transcript summary. Create a summary of the provided transcription. Respond in HTML."""},
            {"role": "user", "content": [
                {"type": "text", "text": f"The audio transcription is: {transcription.text}"}
            ]}
        ]

        response = client.chat.completions.create(model="gpt-4o", messages=messages)
        message_content = response.choices[0].message.content
        session['past'].append(filepath)
        session['generated'].append(message_content)
        session['prompts'].append({"role": "assistant", "content": message_content})
        session.modified = True  # Ensure session is marked as modified
    return redirect(url_for('index'))

