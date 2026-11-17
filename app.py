
import os

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from openai import OpenAI
from dotenv import load_dotenv

from rag import (
    process_pdf,
    extract_text_from_pdf,
    search_relevant_chunks
)

# Project folder configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load API key from project .env file
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

app = Flask(__name__)

# Groq API configuration
api_key = os.getenv("GROQ_API_KEY")

client = None

if api_key:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        timeout=30.0
    )

# Upload folder
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# PDF upload API
@app.route("/upload", methods=["POST"])
def upload_pdf():

    if "file" not in request.files:
        return jsonify({"error": "No file selected"}), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a PDF file"}), 400

    filename = secure_filename(file.filename)

    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        file.save(file_path)

        document_id = process_pdf(file_path)
        extracted_text = extract_text_from_pdf(file_path)

        return jsonify({
            "message": "PDF uploaded successfully!",
            "document_id": document_id,
            "filename": filename,
            "extracted_text": extracted_text
        })

    except Exception as e:
        app.logger.exception("PDF processing failed")
        return jsonify({"error": str(e)}), 500


# Chat API
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}
    question = data.get("message", "").strip()

    if not question:
        return jsonify({
            "reply": "Please enter your question."
        }), 400

    if client is None:
        return jsonify({
            "reply": "GROQ_API_KEY is missing. Please check your .env file."
        }), 500

    try:
        # Include PDF context when available, while allowing general chat.
        chunks = search_relevant_chunks(question)
        context = "\n\n".join(chunks) if chunks else "No PDF context is available."

        # Send question and context to Groq
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful conversational AI assistant. "
                        "Answer greetings and general questions naturally using your "
                        "general knowledge; do not say an answer is missing from a PDF "
                        "for those questions. If the user asks about the uploaded PDF, "
                        "resume, candidate, or its contents, answer only from the "
                        "provided PDF context. If that context does not contain the "
                        "answer, say you could not find it in the uploaded document. "
                        "If no PDF context is available, still answer general questions "
                        "normally. Keep every answer short and simple, usually one "
                        "sentence. For example, describe Python as a high-level, "
                        "interpreted programming language used to build applications, "
                        "websites, automation, and AI. Do not add extra details, lists, "
                        "or examples unless the user asks for them."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Uploaded PDF context:\n{context}\n\n"
                        f"User message: {question}"
                    )
                }
            ]
        )

        answer = response.choices[0].message.content

        return jsonify({
            "reply": answer
        })

    except Exception as e:
        app.logger.exception("Chat request failed")

        # Show actual error during development
        return jsonify({
            "reply": "Chat API error: " + str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
