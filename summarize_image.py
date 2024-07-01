from flask import Blueprint, request, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import base64
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

image_bp = Blueprint('image', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path):
     with open(image_path, "rb") as image_file:
         return base64.b64encode(image_file.read()).decode("utf-8")

@image_bp.route('/summarize', methods=['POST'])
def summarize_image():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join('./data/images', filename)
        file.save(filepath)

        base64_image = encode_image(filepath)
        # Add your image summarization logic here
        session['past'].append(f"Image: {filename}")
        #image_html = f'<a href="{url_for("static", filename="images/" + filename)}" target="_blank"><img src="{url_for("static", filename="images/" + filename)}" style="max-width: 10%;"></a>'
        #session['generated'].append(f"Image summarization result. {image_html}")

        session['prompts'].append({"role": "system", "content": "Always return the answer in HTML format."})
        messages=[
             {"role": "system", "content": "You are a helpful assistant that can identify images."},
             {"role": "user", "content": [
                 {"type": "text", "text": "Describe the image in as much detail as possible.  Always send the answer in HTML format."},
                 {"type": "image_url", "image_url": {
                     "url": f"data:image/png;base64,{base64_image}"}
                 }
             ]}
         ]

        response = client.chat.completions.create(model="gpt-4o", messages=messages)
        message_content = response.choices[0].message.content
        session['past'].append(filepath)
        session['generated'].append(message_content)
        session['prompts'].append({"role": "assistant", "content": message_content})
        session.modified = True  # Ensure session is marked as modified
    return redirect(url_for('index'))

