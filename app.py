from flask import Flask, render_template, session, redirect, url_for
from chat import chat_bp
from summarize_link import link_bp
from summarize_image import image_bp
from summarize_audio import audio_bp
from summarize_video import video_bp
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Register blueprints
app.register_blueprint(chat_bp, url_prefix='/chat')
app.register_blueprint(link_bp, url_prefix='/link')
app.register_blueprint(image_bp, url_prefix='/image')
app.register_blueprint(audio_bp, url_prefix='/audio')
app.register_blueprint(video_bp, url_prefix='/video')

system_role_dict = {"role": "system",
                    "content": "You are a helpful Assistant. Create concise answer with engaging tone. Ask clarifying questions when needed and when you do not know the answer reply with 'I do not know the answer to that question.'. Always return the data in HTML format"}

@app.route('/')
def index():
    if 'prompts' not in session:
        session['prompts'] = [system_role_dict]
    if 'generated' not in session:
        session['generated'] = []
    if 'past' not in session:
        session['past'] = []
    return render_template('index.html', generated=session['generated'], past=session['past'])

@app.route('/new_chat', methods=['GET'])
def new_chat():
    save_conversation()
    session['prompts'] = [system_role_dict]
    session['past'] = []
    session['generated'] = []
    session.modified = True  # Ensure session is marked as modified
    return redirect(url_for('index'))

def save_conversation():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S").replace(':', '_')
    filename = f"{timestamp}.json"
    directory = "./data/conversation_history"
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, filename)
    conversation_history = {
        "prompts": session['prompts'],
        "generated": session['generated'],
        "past": session['past']
    }
    with open(filepath, 'w') as f:
        json.dump(conversation_history, f)

@app.template_filter('zip')
def zip_filter(a, b):
    return zip(a, b)

if __name__ == '__main__':
    for folder in ['images', 'audio', 'videos']:
        if not os.path.exists(folder):
            os.makedirs(folder)
    app.run(port=5005, host="0.0.0.0")

