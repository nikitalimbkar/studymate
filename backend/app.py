
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
import os
import re
import json

from tools import (
    create_study_plan,
    add_task,
    get_tasks,
    complete_task
)


# =========================================
# FLASK SETUP
# =========================================

app = Flask(__name__)
CORS(app)


# =========================================
# GEMINI SETUP
# =========================================

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)


# =========================================
# SIMPLE COMMAND DETECTION
# =========================================

def handle_simple_command(user_message):

    message = user_message.strip()
    lower = message.lower()

    # =========================
    # ADD TASK
    # =========================

    add_patterns = [
        r"add (.+) to my tasks",
        r"add (.+) to my task",
        r"add task (.+)",
        r"add (.+) as a task",
        r"create task (.+)"
    ]

    for pattern in add_patterns:

        match = re.match(pattern, message, re.IGNORECASE)

        if match:

            task = match.group(1).strip()

            result = add_task(task)

            return {
                "title": "Task Added",
                "message": result["message"],
                "tasks": get_tasks()
            }


    # =========================
    # COMPLETE TASK
    # =========================

    complete_patterns = [
        r"complete (.+)",
        r"finish (.+)",
        r"completed (.+)",
        r"mark (.+) as complete",
        r"mark (.+) completed"
    ]

    for pattern in complete_patterns:

        match = re.match(pattern, message, re.IGNORECASE)

        if match:

            task = match.group(1).strip()

            result = complete_task(task)

            return {
                "title": "Task Completed" if result["success"] else "Task Not Found",
                "message": result["message"],
                "tasks": get_tasks()
            }


    # =========================
    # SHOW TASKS
    # =========================

    if lower in [
        "show my tasks",
        "show tasks",
        "my tasks",
        "list my tasks",
        "view tasks"
    ]:

        task_list = get_tasks()

        return {
            "title": "My Tasks",
            "message": "Here are your current tasks.",
            "tasks": task_list
        }


    return None


@app.route("/api/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        user_message = data.get("message", "").strip()


        if not user_message:

            return jsonify({
                "title": "StudyMate",
                "message": "Please enter a message."
            })


        # =====================================
        # FIRST: CHECK SIMPLE COMMAND
        # =====================================

        simple_result = handle_simple_command(user_message)


        if simple_result is not None:

            print("Handled directly:", user_message)

            return jsonify(simple_result)


        # =====================================
        # OTHERWISE USE GEMINI
        # =====================================

        prompt = f"""
You are StudyMate, an AI study assistant.

Student's request:
{user_message}

Understand the student's intention and return ONLY valid JSON.

You can perform these actions:

1. CREATE STUDY PLAN

If the student asks for a study plan, identify:
- Subject
- Number of days
- Hours available per day

Return:

{{
    "action": "create_study_plan",
    "subject": "DBMS",
    "days": 5,
    "hours_per_day": 2
}}


2. ADD TASK

If the student wants to create or add a study task.

Examples:
- "I need to practice Java"
- "I should study SQL"
- "Remind me to practice DSA"
- "Add Practice Java to my tasks"

Return:

{{
    "action": "add_task",
    "task": "Practice Java"
}}


3. SHOW TASKS

If the student wants to see their current tasks.

Examples:
- "Show my tasks"
- "What are my tasks?"
- "What do I need to study?"

Return:

{{
    "action": "get_tasks"
}}


4. COMPLETE TASK

If the student says they finished or completed a task.

Examples:
- "I completed Practice Java"
- "Finish my SQL task"
- "Mark Practice Java as complete"

Return:

{{
    "action": "complete_task",
    "task": "Practice Java"
}}


5. GENERAL STUDY QUESTION

If the student asks a general study-related question, return:

{{
    "action": "ask_question",
    "question": "the student's question",
    "answer": "a simple, clear, student-friendly answer"
}}


If there is not enough information, ask a question using:

{{
    "action": "ask_question",
    "question": "your question here",
    "answer": "Please provide more information so I can help you."
}}

Do not add markdown.
Do not add explanations outside the JSON.
"""


        response = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt
        )


        print("AI response:")
        print(response)


        # =====================================
        # GET GEMINI TEXT
        # =====================================

        ai_text = response.output_text.strip()

        print("AI JSON:")
        print(ai_text)


        # Remove possible markdown fences
        ai_text = ai_text.replace("```json", "")
        ai_text = ai_text.replace("```", "")
        ai_text = ai_text.strip()


        ai_data = json.loads(ai_text)


        # =====================================
        # CREATE STUDY PLAN
        # =====================================

        if ai_data.get("action") == "create_study_plan":

            plan = create_study_plan(
                ai_data["subject"],
                int(ai_data["days"]),
                float(ai_data["hours_per_day"])
            )

            return jsonify({
                "title": "StudyMate Study Plan",
                "message": "I created a personalized study plan for you.",
                "plan": plan
            })


        # =====================================
        # ADD TASK
        # =====================================

        if ai_data.get("action") == "add_task":

            result = add_task(ai_data["task"])

            return jsonify({
                "title": "Task Added",
                "message": result["message"],
                "tasks": get_tasks()
            })


        # =====================================
        # GET TASKS
        # =====================================

        if ai_data.get("action") == "get_tasks":

            task_list = get_tasks()

            return jsonify({
                "title": "My Tasks",
                "message": "Here are your current tasks.",
                "tasks": task_list
            })


        # =====================================
        # COMPLETE TASK
        # =====================================

        if ai_data.get("action") == "complete_task":

            result = complete_task(ai_data["task"])

            return jsonify({
                "title": "Task Completed" if result["success"] else "Task Not Found",
                "message": result["message"],
                "tasks": get_tasks()
            })


        # =====================================
        # GENERAL QUESTION
        # =====================================

        if ai_data.get("action") == "ask_question":

            question = ai_data.get(
                "question",
                user_message
            )

            answer = ai_data.get(
                "answer",
                "I couldn't generate an answer."
            )

            return jsonify({
                "title": "StudyMate Answer",
                "message": answer
            })


        # =====================================
        # UNKNOWN ACTION
        # =====================================

        return jsonify({
            "title": "StudyMate",
            "message": "I unde"
            "rstood your request, but I couldn't determine the action."
        })


    except Exception as e:

        print("Error:", e)

    error_message = str(e)

    if "503" in error_message or "high demand" in error_message:
        return jsonify({
            "title": "Gemini temporarily unavailable",
            "message": "The AI service is temporarily busy. Please try again later."
        }), 503

    return jsonify({
        "title": "StudyMate Error",
        "message": "Something went wrong while processing your request."
    }), 500


# =========================================
# RUN SERVER
# =========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

