from flask import Blueprint, request, session, redirect, url_for
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

link_bp = Blueprint('link', __name__)

def fetch_website_content(url):
     """Fetch the content of the website."""
     response = requests.get(url)
     soup = BeautifulSoup(response.content, 'html.parser')

     # Extract text from the BeautifulSoup object. You might need to adjust tags for better results.
     text = ' '.join([p.text for p in soup.find_all('p')])
     return text


@link_bp.route('/summarize', methods=['POST'])
def summarize_link():
    link_input = request.form['user_input']
    if link_input:
        website_data = fetch_website_content(link_input)
        session['prompts'].append({"role": "system", "content": "Always return the answer in HTML format."})
        session['prompts'].append({"role": "user", "content": website_data})
        response = client.chat.completions.create(model="gpt-4o", messages=session['prompts'])
        message_content = response.choices[0].message.content
        session['past'].append(link_input)
        session['generated'].append(message_content)
        session['prompts'].append({"role": "assistant", "content": message_content})
        session.modified = True  # Ensure session is marked as modified
    return redirect(url_for('index'))

