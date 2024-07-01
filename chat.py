from flask import Blueprint, request, session, redirect, url_for
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

chat_bp = Blueprint('chat', __name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@chat_bp.route('/send', methods=['POST'])
def send_chat():
    chat_input = request.form['user_input']
    if chat_input:
        session['prompts'].append({"role": "user", "content": chat_input})
        response = client.chat.completions.create(model="gpt-4o", messages=session['prompts'])
        message_content = response.choices[0].message.content
        session['past'].append(chat_input)
        session['generated'].append(message_content)
        session['prompts'].append({"role": "assistant", "content": message_content})
        session.modified = True  # Ensure session is marked as modified
    return redirect(url_for('index'))

