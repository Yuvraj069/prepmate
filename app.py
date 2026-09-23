import os
import uuid
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, Response, flash, redirect, render_template, request, session, url_for

from services.ai_coach import InterviewCoach
from services.auth import AuthService
from services.voice import VoiceService

# Override blank starter entries when a user adds updated values later in .env.
load_dotenv(override=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-this-in-production")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

auth = AuthService()
coach = InterviewCoach()
voice = VoiceService()


def signed_in(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            flash("Please sign in to continue.", "notice")
            return redirect(url_for("auth_page"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_shell_data():
    return {"current_year": datetime.now().year, "voice_available": voice.configured}


@app.route("/", methods=["GET", "POST"])
def auth_page():
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        mode = request.form.get("mode", "login")
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()

        if not email or not password or (mode == "register" and not name):
            flash("Complete all required fields to continue.", "error")
            return render_template("auth.html", mode=mode)

        result = auth.register(email, password, name) if mode == "register" else auth.login(email, password)
        if result.ok:
            session["user"] = result.user
            session["session_token"] = result.token
            session["session_started"] = datetime.now().isoformat()
            return redirect(url_for("dashboard"))
        flash(result.message, "error")
        return render_template("auth.html", mode=mode)

    return render_template("auth.html", mode=request.args.get("mode", "login"))


@app.route("/logout")
def logout():
    auth.logout(session.get("session_token"))
    session.clear()
    flash("You have been signed out.", "notice")
    return redirect(url_for("auth_page"))


@app.route("/dashboard")
@signed_in
def dashboard():
    return render_template("dashboard.html", user=session["user"], interviews=coach.interview_tracks())


@app.route("/practice/<track_id>", methods=["GET", "POST"])
@signed_in
def practice(track_id):
    track = coach.get_track(track_id)
    if not track:
        flash("That interview track is not available.", "error")
        return redirect(url_for("dashboard"))

    history_key = f"practice_{track_id}"
    history = session.get(history_key, [])
    if not history:
        history = [{"role": "coach", "content": coach.opening_question(track), "kind": "question"}]
        session[history_key] = history

    if request.method == "POST":
        answer = request.form.get("answer", "").strip()
        if answer:
            history.append({"role": "you", "content": answer, "kind": "answer"})
            reply = coach.evaluate_answer(track, answer, history)
            history.append({"role": "coach", "content": reply, "kind": "feedback"})
            session[history_key] = history[-12:]
        return redirect(url_for("practice", track_id=track_id))
    return render_template("practice.html", user=session["user"], track=track, history=history)


@app.route("/ask", methods=["GET", "POST"])
@signed_in
def ask():
    chat = session.get("coach_chat", [])
    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()
        if prompt:
            chat.append({"role": "you", "content": prompt})
            chat.append({"role": "coach", "content": coach.answer_question(prompt, chat)})
            session["coach_chat"] = chat[-14:]
        return redirect(url_for("ask"))
    return render_template("ask.html", user=session["user"], chat=chat)


@app.route("/voice/synthesize", methods=["POST"])
@signed_in
def synthesize():
    text = request.form.get("text", "").strip()
    if not text:
        flash("There is no response to read aloud.", "notice")
        return redirect(request.referrer or url_for("dashboard"))
    audio = voice.synthesize(text)
    if not audio:
        flash("Add Azure Speech settings to enable spoken coaching.", "notice")
        return redirect(request.referrer or url_for("dashboard"))
    return Response(audio, mimetype="audio/mpeg", headers={"Content-Disposition": "inline; filename=prepmate-coach.mp3"})


@app.route("/voice/transcribe", methods=["POST"])
@signed_in
def transcribe():
    upload = request.files.get("audio")
    if not upload or not upload.filename:
        flash("Choose an audio file to transcribe.", "error")
        return redirect(request.referrer or url_for("dashboard"))
    filename = f"{uuid.uuid4()}-{upload.filename}"
    transcription = voice.transcribe(upload, filename)
    if transcription:
        flash(f"Transcript: {transcription}", "notice")
    else:
        flash("Voice transcription needs Azure Speech configuration.", "notice")
    return redirect(request.referrer or url_for("dashboard"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
