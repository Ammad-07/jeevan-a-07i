from flask import Flask, render_template, redirect, url_for, request, session
import random
import cv2
from deepface import DeepFace

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Define intents + responses
responses = {
    'greeting': ["Hello! I'm Jeevan AI. How are you feeling today?"],
    'sad_feelings': ["I'm really sorry you're feeling this way. Want to talk about it?"],
    'positive_feelings': ["That's great to hear! 😊"],
    'confusion': ["Feeling confused is okay. Let's take a deep breath together."],
    'anxiety': ["It’s okay to feel anxious sometimes. You’re not alone."],
    'life_events': ["That sounds really tough. I'm here to support you."],
    'frustration': ["It seems like you’re frustrated. I’m here to listen."],
    'anger': ["It seems like you're really angry. Want to share what's bothering you?"],
    'fear': ["It's okay to be afraid sometimes. You're safe here."],
    'love': ["Love is a powerful emotion. It can make life wonderful. How can I help?"],
    'hope': ["I know things are tough, but there's always hope. You're not alone."],
    'motivation': ["You’ve got this! Keep going, you’re stronger than you think."],
    'thank_you': ["You're welcome! I'm here for you anytime."],
    'joke': ["Why don’t skeletons fight each other? They don’t have the guts! 😄"],
    'generic': ["I'm here for you. Please tell me more."],
    'career_help': ["I'm sorry you're going through this. Do you want advice on your career?"],
    'relationship_help': ["I understand relationships can be hard sometimes. Want to talk about it?"],
    'feeling_fine': ["Glad to hear you're doing okay. Let me know if you want to talk."],
    'not_feeling_good': ["I'm really sorry to hear that. You're not alone — I'm here for you. If things feel overwhelming, consider reaching out to a mental health professional."],
    'suicidal_thoughts': ["It sounds like you're in a lot of pain. You're not alone. Please talk to someone immediately — contact a trusted person or a mental health helpline."],
    'motivational_quote': ["“Every day may not be good... but there's something good in every day.” – Alice Morse Earle"],
    'breathing_exercise': ["Try this: Inhale slowly for 4 seconds, hold for 4 seconds, exhale for 4 seconds. Repeat this a few times. Let’s breathe together."],
    'how_are_you': ["I'm just a chatbot, but I’m always ready to help you. How are *you* feeling today?"],
    'stress': ["Stress can be really overwhelming. Want to try a breathing exercise or talk about it?"],
    'panic': ["You're having a tough moment. Try grounding yourself by noticing 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste."],
    'lonely': ["You are not alone. I'm here for you whenever you need to talk."],
    'sleep_trouble': ["Sleep issues can be tough. Try winding down with a calming activity and avoid screens before bed."],
    'exercise': ["Physical activity can help you feel better. Even a short walk or stretching can improve your mood."]
}

# Emotion to calming GIF mapping
emotion_gifs = {
    'sad': "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExbzMwOTk5dGRyc2psdjFnNzk1ZTNyY2xyMTU3NHdpMmFnc3ppNWxidyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/6gDSyjaOPwZ4A/giphy.gif",
    'angry': "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExb2lla2hveHZ0dDYxM2tjYnliZXQxcGxmd2RqOWlueTBqY2Y1bWpyOSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/MLhIi4DoxeUjC/giphy.gif",
    'fear': "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExZjBlbDIzb3VtY2JhcnQya2Z4Zjc2YXc0cnd1aTVqdmc4eDczYm1zNSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/4xJdgCm2ZQoFRZtczB/giphy.gif",
    'anxious': "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMm5kaDEzY29uNHBiOXpnc3NuYWJnbTB0Yjc0OXhxMGczYjNhM3hscSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0K4ahtipypSs6M0M/giphy.gif",
    'frustrated': "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExOTUxcGduZ3N5MTJoYXgyOWV1a241YjVpZ3NjcWJybXZmdzJ6d3VkdSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/h36vh423PiV9K/giphy.gif",
    'neutral': "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExaGhzNTNoc3Rpc2s0N3FreHJpdWg4dW02a3l4M2NqOHU2YnVna2R4cyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/LMJavgUFMwM6CICHrt/giphy.gif"
}

def detect_intent(user_message):
    user_message = user_message.lower()

    if any(word in user_message for word in ["hello", "hi", "hey"]):
        return 'greeting'
    elif "how are you" in user_message:
        return 'how_are_you'
    elif any(word in user_message for word in ["fine", "okay", "doing well", "not bad"]):
        return 'feeling_fine'
    elif any(word in user_message for word in ["not feeling good", "i feel bad", "upset", "i feel terrible", "i feel sick"]):
        return 'not_feeling_good'
    elif any(word in user_message for word in ["die", "kill myself", "suicide", "end it", "give up", "i'm going to die"]):
        return 'suicidal_thoughts'
    elif any(word in user_message for word in ["motivate me", "motivation quote", "inspire me", "i need motivation"]):
        return 'motivational_quote'
    elif any(word in user_message for word in ["breathing", "breathe", "relax", "calm down"]):
        return 'breathing_exercise'
    elif any(word in user_message for word in ["sad", "low", "unhappy", "depressed", "down"]):
        return 'sad_feelings'
    elif any(word in user_message for word in ["happy", "great", "awesome", "amazing"]):
        return 'positive_feelings'
    elif any(word in user_message for word in ["confused", "don't know", "unsure"]):
        return 'confusion'
    elif any(word in user_message for word in ["anxious", "worried", "scared", "nervous"]):
        return 'anxiety'
    elif any(word in user_message for word in ["lost job", "breakup", "fired", "accident", "died"]):
        return 'life_events'
    elif any(word in user_message for word in ["frustrated", "angry", "pissed"]):
        return 'frustration'
    elif any(word in user_message for word in ["anger", "rage", "mad"]):
        return 'anger'
    elif any(word in user_message for word in ["fear", "afraid", "scared"]):
        return 'fear'
    elif any(word in user_message for word in ["love", "romantic", "heart"]):
        return 'love'
    elif any(word in user_message for word in ["hope", "future", "believe"]):
        return 'hope'
    elif any(word in user_message for word in ["motivate", "inspire", "keep going"]):
        return 'motivation'
    elif any(word in user_message for word in ["thank you", "thanks", "thankful"]):
        return 'thank_you'
    elif any(word in user_message for word in ["joke", "funny", "laugh"]):
        return 'joke'
    elif any(word in user_message for word in ["panic", "can't breathe", "hyperventilating"]):
        return 'panic'
    elif any(word in user_message for word in ["alone", "lonely", "no one"]):
        return 'lonely'
    elif any(word in user_message for word in ["can't sleep", "sleep trouble", "insomnia"]):
        return 'sleep_trouble'
    elif any(word in user_message for word in ["exercise", "workout", "walk", "gym"]):
        return 'exercise'
    else:
        return 'generic'

# Emotion detection
def detect_emotion_once():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        return "neutral"

    try:
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        emotion = result[0]['dominant_emotion']
        print("[Detected Emotion]:", emotion)
        return emotion
    except:
        return "neutral"

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/start")
def start():
    emotion = detect_emotion_once()
    session['emotion'] = emotion

    if emotion.lower() == "happy":
        return redirect(url_for("result"))

    return redirect(url_for("chatbot"))

@app.route("/result")
def result():
    return render_template("result.html")

@app.route("/chatbot", methods=['GET', 'POST'])
def chatbot():
    emotion = session.get('emotion', 'neutral')
    gif_url = emotion_gifs.get(emotion.lower(), None)

    user_message = None
    bot_response = None
    chat_history = []

    if request.method == 'POST':
        user_message = request.form['user_message']
        intent = detect_intent(user_message)
        bot_response = random.choice(responses[intent])
        chat_history.append({'user': user_message, 'bot': bot_response})

    return render_template("bot.html",
                           chat_history=chat_history,
                           emotion=emotion,
                           gif_url=gif_url)

if __name__ == "__main__":
    app.run(debug=True)
