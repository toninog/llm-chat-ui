from flask import Blueprint, request, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

audio_bp = Blueprint('audio', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'aac'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@audio_bp.route('/summarize', methods=['POST'])
def summarize_audio():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join('./data/audio', filename)
        file.save(filepath)

        # now do the AUDIO
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(filepath, "rb"),
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

