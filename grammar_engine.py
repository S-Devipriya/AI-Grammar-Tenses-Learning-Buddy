import google.generativeai as genai
import json
import streamlit as st

def generate_quiz_data(tense_name, api_key_val, is_assessment=False):
    genai.configure(api_key=api_key_val)
    model = genai.GenerativeModel("gemini-3.5-flash")

    num_questions = 15 if is_assessment else 5
    scope_instruction = (
        "Create a comprehensive 15-question diagnostic multiple-choice quiz testing the user across the entire spectrum of English grammar tenses (Past, Present, and Future variants randomly distributed)."
        if is_assessment else
        f"Create a focused 5-question multiple-choice quiz testing the user's explicit understanding of the tense: '{tense_name}'."
    )

    prompt = f"""
    {scope_instruction}

    You must respond ONLY with a valid JSON array of objects. Do not include markdown formatting like ```json.
    Each object in the array must have exactly these keys:
    - "question": The fill-in-the-blank sentence or evaluation query.
    - "options": An array of 4 distinct string choices.
    - "correct_answer": The exact string match from the options array.
    - "explanation": A 2-sentence breakdown detailing why the correct answer fits and why common errors fail.
    - "tense_category": The exact name of the specific tense tested by this question (e.g., 'Present Perfect Continuous', 'Simple Past', 'Future Perfect').
    """

    try:
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_text)
    except Exception as e:
        st.error("Failed to parse quiz payload. Please re-trigger generation.")
        return []

def generate_macro_feedback(tense_name, score, total, history, api_key_val, is_assessment=False):
    genai.configure(api_key=api_key_val)
    model = genai.GenerativeModel("gemini-3.5-flash")

    if is_assessment:
        summary_context = f"The user completed a 15-question global diagnostic assessment. They scored {score}/{total}. Here is the breakdown of the specific question metrics they failed: {json.dumps(history)}."
        goal_instruction = "Analyze their patterns of error, identify structural timeline blind spots, and give them a customized 3-step dynamic study recommendations list pointing to specific tenses to review."
    else:
        summary_context = f"The user completed a targeted quiz on '{tense_name}'. They scored {score}/{total}. Error log context: {json.dumps(history)}."
        goal_instruction = "Provide a warm, supportive, 3-sentence summary highlighting what they did well and offering a targeted micro-tip on how to avoid these specific tense errors going forward."

    prompt = f"""
    Context: {summary_context}
    Role: You are Twig, a brilliant, adaptive, and highly encouraging AI Learning Buddy.
    Task: {goal_instruction}

    Format your response cleanly using markdown bullets. Do not use generic introductory sentences. Go straight into the critique.
    """
    response = model.generate_content(prompt)
    return response.text