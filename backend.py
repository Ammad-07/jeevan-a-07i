from flask import Flask, render_template, redirect, url_for, request, session, jsonify
import random
import cv2
from deepface import DeepFace
import json
import os

PROGRESS_FILE = "progress_data.json"

def load_user_progress(user_id):
    if not os.path.exists(PROGRESS_FILE):
        print("load_user_progress - No progress file found, returning empty dict")
        return {}

    try:
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
        print("load_user_progress - Loaded progress for user_id:", user_id, "Data:", data.get(user_id, {}))
        return data.get(user_id, {})
    except Exception as e:
        print("load_user_progress - Error loading progress file:", str(e))
        return {}

def save_user_progress(user_id, progress_data):
    print("save_user_progress - Saving progress for user_id:", user_id)
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {}
        
        # Save progress under the user's email (user_id)
        data[user_id] = progress_data

        with open(PROGRESS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print("save_user_progress - Progress saved successfully:", progress_data)
    except Exception as e:
        print("save_user_progress - Error saving progress:", str(e))

app = Flask(__name__)
app.secret_key = 'supersecretkey'

@app.route("/", methods=['GET'])
def index():
    print("Index route - Session contents:", session)
    session.clear()
    print("Index route - Session cleared, redirecting to login")
    return redirect(url_for('login'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    print("Login route - Accessed with method:", request.method)
    if request.method == 'POST':
        print("Login route - Processing POST request")
        # Handle JSON request from frontend
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            print("Login route - JSON request: email=", email)
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            print("Login route - Form request: email=", email)

        # Load users from JSON
        try:
            with open("users.json", "r") as f:
                users = json.load(f)
            print("Login route - Loaded users.json")
        except FileNotFoundError:
            users = {}
            print("Login route - users.json not found, using empty users dict")

        if email in users and users[email]["password"] == password:
            session['user_id'] = email
            session['user_name'] = users[email].get("name", "User")
            session.modified = True
            print("Login route - Successful login for", email, "Session:", session)
            if request.is_json:
                print("Login route - Returning JSON response with redirect to home")
                return jsonify({"message": "Login successful", "redirect": url_for("home", _external=False)}), 200
            print("Login route - Redirecting to home")
            return redirect(url_for("home"))
        else:
            error = "Invalid email or password."
            print("Login route - Login failed:", error)
            if request.is_json:
                return jsonify({"message": error}), 401
            return render_template("login.html", error=error)

    print("Login route - Rendering login.html")
    return render_template("login.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Handle JSON request from frontend
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')
        else:
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')

        # Load users from JSON
        try:
            with open("users.json", "r") as f:
                users = json.load(f)
        except FileNotFoundError:
            users = {}

        # Check if email already exists
        if email in users:
            error = "Email already registered."
            if request.is_json:
                return jsonify({"message": error}), 400
            return render_template("signup.html", error=error)

        # Save new user
        users[email] = {"name": name, "password": password}
        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)

        if request.is_json:
            return jsonify({"message": "Sign up successful"}), 200
        return redirect(url_for("login"))

    return render_template("signup.html")

# Predefined responses (unchanged)
responses = {
    'greeting': ["Hello! I'm Jeevan AI. How are you feeling today?"],
    'sad_feelings': ["I'm really sorry you're feeling this way. Want to talk about it?"],
    'positive_feelings': ["That's great to hear! 😊"],
    'confusion': ["Feeling confused is okay. Let's take a deep breath together."],
    'anxiety': ["It's okay to feel anxious sometimes. You're not alone."],
    'life_events': ["That sounds really tough. I'm here to support you."],
    'frustration': ["It seems like you're frustrated. I'm here to listen."],
    'anger': ["It seems like you're really angry. Want to share what's bothering you?"],
    'fear': ["It's okay to be afraid sometimes. You're safe here."],
    'love': ["Love is a powerful emotion. It can make life wonderful. How can I help?"],
    'hope': ["I know things are tough, but there's always hope. You're not alone."],
    'motivation': ["You've got this! Keep going, you're stronger than you think."],
    'thank_you': ["You're welcome! I'm here for you anytime."],
    'joke': ["Why don't skeletons fight each other? They don't have the guts! 😄"],
    'generic': ["I'm here for you. Please tell me more."],
    'career_help': ["I'm sorry you're going through this. Do you want advice on your career?"],
    'relationship_help': ["I understand relationships can be hard sometimes. Want to talk about it?"],
    'feeling_fine': ["Glad to hear you're doing okay. Let me know if you want to talk."],
    'not_feeling_good': ["I'm really sorry to hear that. You're not alone — I'm here for you. If things feel overwhelming, consider reaching out to a mental health professional."],
    'suicidal_thoughts': ["It sounds like you're in a lot of pain. You're not alone. Please talk to someone immediately — contact a trusted person or a mental health helpline."],
    'motivational_quote': ["'Every day may not be good... but there's something good in every day.' – Alice Morse Earle"],
    'breathing_exercise': ["Try this: Inhale slowly for 4 seconds, hold for 4 seconds, exhale for 4 seconds. Repeat this a few times. Let's breathe together."],
    'how_are_you': ["I'm just a chatbot, but I'm always ready to help you. How are *you* feeling today?"],
    'stress': ["Stress can be really overwhelming. Want to try a breathing exercise or talk about it?"],
    'panic': ["You're having a tough moment. Try grounding yourself by noticing 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste."],
    'lonely': ["You are not alone. I'm here for you whenever you need to talk."],
    'sleep_trouble': ["Sleep issues can be tough. Try winding down with a calming activity and avoid screens before bed."],
    'exercise': ["Physical activity can help you feel better. Even a short walk or stretching can improve your mood."]
}

# Emotion to GIF mapping (unchanged)
emotion_gifs = {
    'sad': "https://media4.giphy.com/media/6gDSyjaOPwZ4A/giphy.gif",
    'angry': "https://media1.giphy.com/media/MLhIi4DoxeUjC/giphy.gif",
    'fear': "https://media0.giphy.com/media/4xJdgCm2ZQoFRZtczB/giphy.gif",
    'anxious': "https://media1.giphy.com/media/l0K4ahtipypSs6M0M/giphy.gif",
    'frustrated': "https://media0.giphy.com/media/h36vh423PiV9K/giphy.gif",
    'neutral': "https://media2.giphy.com/media/LMJavgUFMwM6CICHrt/giphy.gif"
}

# Load daily challenges (unchanged)
def load_daily_challenges():
    with open("daily_challenges.json", "r") as f:
        return json.load(f)

def detect_intent(user_message):
    user_message = user_message.lower()

    if any(word in user_message for word in ["hello", "hi", "hey"]):
        return "greeting"
    elif any(word in user_message for word in ["sad", "unhappy", "depressed", "cry"]):
        return "sad_feelings"
    elif any(word in user_message for word in ["happy", "joy", "good", "great"]):
        return "positive_feelings"
    elif any(word in user_message for word in ["confused", "unsure", "puzzled"]):
        return "confusion"
    elif any(word in user_message for word in ["anxious", "nervous", "worried"]):
        return "anxiety"
    elif any(word in user_message for word in ["lost job", "divorce", "failed", "fired"]):
        return "life_events"
    elif any(word in user_message for word in ["frustrated", "annoyed"]):
        return "frustration"
    elif any(word in user_message for word in ["angry", "mad", "furious"]):
        return "anger"
    elif any(word in user_message for word in ["scared", "afraid", "fear"]):
        return "fear"
    elif any(word in user_message for word in ["love", "loving"]):
        return "love"
    elif any(word in user_message for word in ["hope", "hopeful"]):
        return "hope"
    elif any(word in user_message for word in ["motivate", "motivation", "energize"]):
        return "motivation"
    elif any(word in user_message for word in ["thank", "thanks"]):
        return "thank_you"
    elif "joke" in user_message:
        return "joke"
    elif any(word in user_message for word in ["career", "job", "work"]):
        return "career_help"
    elif any(word in user_message for word in ["relationship", "breakup", "partner"]):
        return "relationship_help"
    elif any(word in user_message for word in ["fine", "okay", "alright"]):
        return "feeling_fine"
    elif any(word in user_message for word in ["not good", "bad", "terrible"]):
        return "not_feeling_good"
    elif any(word in user_message for word in ["suicide", "kill myself", "end my life"]):
        return "suicidal_thoughts"
    elif any(word in user_message for word in ["quote", "inspire", "wisdom"]):
        return "motivational_quote"
    elif any(word in user_message for word in ["breathe", "breathing", "exercise"]):
        return "breathing_exercise"
    elif "how are you" in user_message:
        return "how_are_you"
    elif "stress" in user_message:
        return "stress"
    elif "panic" in user_message:
        return "panic"
    elif "lonely" in user_message or "alone" in user_message:
        return "lonely"
    elif any(word in user_message for word in ["can't sleep", "sleep problem", "insomnia"]):
        return "sleep_trouble"
    elif "exercise" in user_message or "workout" in user_message:
        return "exercise"
    else:
        return "generic"

# Emotion detection from webcam (unchanged)
def detect_emotion_once():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        return "neutral"

    try:
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        emotion = result[0]['dominant_emotion']
        return emotion
    except:
        return "neutral"

@app.route("/challenges", methods=['GET', 'POST'])
def challenges():
    if 'user_id' not in session:
        print("Challenges route - No user_id in session, redirecting to login")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    print("Challenges route - User ID:", user_id)
    emotion = session.get('emotion', 'neutral')
    daily_challenges = load_daily_challenges()
    challenges_for_today = daily_challenges.get(emotion.lower(), [])

    # Load saved progress for the current user
    user_progress = load_user_progress(user_id)
    completed_tasks = user_progress.get('completed_tasks', [])
    xp = user_progress.get('xp', 0)
    streak = user_progress.get('streak', 0)
    badges = user_progress.get('badges', [])
    level = xp // 100

    if request.method == 'POST':
        completed_tasks = request.form.getlist('completed_tasks')
        xp_reward = len(completed_tasks) * 10
        xp += xp_reward
        streak += 1
        
        # Badge logic
        if xp >= 50 and "Wellness Starter" not in badges:
            badges.append("Wellness Starter")

        # Save progress for the current user
        user_progress = {
            'completed_tasks': completed_tasks,
            'xp': xp,
            'streak': streak,
            'badges': badges
        }
        save_user_progress(user_id, user_progress)

        return redirect(url_for('home'))

    return render_template(
        "challenge.html",
        challenges=challenges_for_today,
        completed_tasks=completed_tasks,
        progress=len(completed_tasks),
        total=len(challenges_for_today),
        streak=streak,
        xp=xp,
        level=level,
        badges=badges
    )

@app.route("/start")
def start():
    print("Start route - WARNING: This should not be called after login")
    print("Start route - Detecting emotion")
    emotion = detect_emotion_once()
    session['emotion'] = emotion
    print("Start route - Emotion detected:", emotion)

    if emotion.lower() == "happy":
        print("Start route - Redirecting to result")
        return redirect(url_for("result"))

    print("Start route - Redirecting to chatbot")
    return redirect(url_for("chatbot"))

@app.route("/result")
def result():
    print("Result route - Rendering result.html")
    return render_template("result.html")

@app.route("/home", methods=['GET', 'POST'])
def home():
    print("Home route - Accessed with session:", session)
    if 'user_id' not in session:
        print("Home route - No user_id in session, redirecting to login")
        return redirect(url_for('login'))

    emotion = session.get('emotion', 'neutral')
    gif_url = emotion_gifs.get(emotion.lower(), None)
    print("Home route - Emotion:", emotion, "GIF URL:", gif_url)

    if request.method == 'POST':
        user_message = request.form['user_message']
        intent = detect_intent(user_message)
        print("Home route - User message:", user_message, "Intent:", intent)

        if intent:
            bot_response = random.choice(responses[intent])
        else:
            bot_response = "I'm here for you. Please tell me more."
        print("Home route - Bot response:", bot_response)

        return render_template("home.html",
                               bot_response=bot_response,
                               emotion=emotion,
                               gif_url=gif_url)

    print("Home route - Rendering home.html")
    return render_template("home.html", emotion=emotion, gif_url=gif_url)

@app.route("/bot", methods=['GET', 'POST'])
def chatbot():
    print("Chatbot route - Accessed with session:", session)
    if 'user_id' not in session:
        print("Chatbot route - No user_id in session, redirecting to login")
        return redirect(url_for('login'))

    emotion = session.get('emotion', 'neutral')
    gif_url = emotion_gifs.get(emotion.lower(), None)
    print("Chatbot route - Emotion:", emotion, "GIF URL:", gif_url)

    session.setdefault('xp', 0)
    session.setdefault('chat_history', [])

    if request.method == 'POST':
        user_message = request.form['user_message']
        intent = detect_intent(user_message)
        print("Chatbot route - User message:", user_message, "Intent:", intent)

        if intent:
            bot_response = random.choice(responses[intent])
        else:
            bot_response = "I'm here for you. Please tell me more."
        print("Chatbot route - Bot response:", bot_response)

        session['chat_history'].append({'user': user_message, 'bot': bot_response})
        session.modified = True
        print("Chatbot route - Updated chat history:", session['chat_history'])

    return render_template(
        "bot.html",
        chat_history=session.get('chat_history', []),
        emotion=emotion,
        gif_url=gif_url
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    app.run(debug=True)