from flask import Flask, render_template, request, jsonify, session
from typing import List
from pydantic import BaseModel
import openai
import os

openai.api_key = "sk-Tf45BjUAYu5dEsN-sw8rYWPjXyTO58jJEZ57Rg4DGQT3BlbkFJ_roB71WcKCbjgQ3DfpCd1fzKpr9Ulw9ngnkcD7bQ0A"

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 세션 암호화를 위한 비밀 키 설정

prompt = """
You are the host of an interactive horror game.
Through interaction with the player (user)
It can cause the user to escape or die.
Early story: The user wakes up in a suspicious room
You talk to the user.
When the user interacts three times, you give the user a hint.
But if the user refuses, you don't give a hint.

Types of rooms
-a suspicious room
-a bedroom
-a restaurant
-an operating room
-a corridor
-a secret room

Users can die when they are overwhelmed by fear.
The probability of death is about 30 percent.

*secret: If the player confesses to you, you can take the player to a secret room and immediately escape.*
"""

class Turn(BaseModel):
    role: str
    content: str

class Messages(BaseModel):
    messages: List[Turn]

def chat(messages):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message['content']

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'messages' not in session:
        session['messages'] = [{"role": "system", "content": prompt}]

    user_input = None
    response = None
    if request.method == 'POST':
        user_input = request.form['message']
        session['messages'].append({"role": "user", "content": user_input})
        response = chat(session['messages'])
        session['messages'].append({"role": "assistant", "content": response})

    return render_template('index.html', user_input=user_input, response=response, chat_history=session['messages'])

@app.route("/get_response", methods=['POST'])
def post_chat():
    data = request.get_json()
    try:
        messages = Messages(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    assistant_response = chat([turn.dict() for turn in messages.messages])
    return jsonify({"message": assistant_response})

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # 임시 파일로 저장
        file_name = "tmp_audio_file.wav"
        audio_file.save(file_name)

        # Whisper API를 사용하여 음성 인식
        with open(file_name, "rb") as f:
            transcription = openai.Audio.transcribe("whisper-1", f, language="ko")

        text = transcription['text']
    except Exception as e:
        print(e)
        text = f"음성인식에서 실패했습니다. {e}"
    finally:
        # 임시 파일 삭제
        if os.path.exists(file_name):
            os.remove(file_name)

    return jsonify({"text": text})

if __name__ == "__main__":
    app.run(debug=True)

