import streamlit as st
import google.generativeai as genai
from grammar_engine import generate_quiz_data, generate_macro_feedback

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Grammar Tense Learning Buddy", page_icon="📚", layout="centered")
st.title("📚 Grammar Tense Learning Buddy")
st.write("Master English tenses through bite-sized breakdowns and interactive practice with your study buddy Twig!")

api_key = st.secrets["GEMINI_API_KEY"]

# --- SESSION STATE INITIALIZATION ---
for key, default in [
    ("quiz_questions", []), ("current_question_idx", 0), ("score", 0),
    ("quiz_submitted", False), ("quiz_active", False), ("wrong_answers_history", []),
    ("explanation_sections", []), ("current_card_idx", 0), ("current_view", None),
    ("examples_text", ""), ("macro_feedback", "")
]:
    if key not in st.session_state: st.session_state[key] = default

# --- ACTIVITY MODE SELECTION ---
option = st.selectbox("Choose an Activity:", ["Break Down Concept", "Read Real-Life Examples", "Take Interactive Quiz", "Get Assessment Feedback"])

selected_tense = None
if option != "Get Assessment Feedback":
    st.markdown("### 🎯 Choose Your Target Tense")
    main_category = st.selectbox("Select Time Horizon:", ["-- Select --", "Present", "Past", "Future"])
    sub_tenses = ["Simple", "Continuous", "Perfect", "Perfect Continuous"]
    if main_category != "-- Select --":
        chosen_sub = st.radio(f"Choose the specific {main_category} Tense form:", sub_tenses, horizontal=True)
        selected_tense = f"Simple {main_category}" if chosen_sub == "Simple" else f"{main_category} {chosen_sub}"
    if selected_tense: st.info(f"Active Focus: **{selected_tense}**")
    else: st.warning("Please select a time horizon and sub-tense from above to get started.")
else:
    st.info("🚀 **Global Diagnostic Mode Active:** 15-question mixed assessment.")
    selected_tense = "All Tenses Comprehensive Assessment"

# --- CONTROLLER ACTIONS ---
if st.button("✨ Start Activity", type="primary") and (selected_tense or option == "Get Assessment Feedback"):
    if not api_key:
        st.error("Please provide an API key.")
    else:
        st.session_state.quiz_active = False
        st.session_state.current_view = None
        st.session_state.macro_feedback = ""
        st.session_state.wrong_answers_history = []

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.5-flash")

        with st.spinner("Loading..."):
            if option == "Break Down Concept":
                prompt = f"Provide a structural breakdown of '{selected_tense}' split into 3 parts separated by '---SECTION---'. Part 1: Blueprint & Analogy. Part 2: Affirmative/Negative/Interrogative formulas. Part 3: Signals/Time markers."
                res = model.generate_content(prompt)
                st.session_state.explanation_sections = [s.strip() for s in res.text.split("---SECTION---") if s.strip()]
                st.session_state.current_card_idx = 0
                st.session_state.current_view = "concept"
            elif option == "Read Real-Life Examples":
                prompt = f"Provide 4 distinct natural dialogue examples using '{selected_tense}' and note speaker intent."
                st.session_state.examples_text = model.generate_content(prompt).text
                st.session_state.current_view = "examples"
            elif option in ["Take Interactive Quiz", "Get Assessment Feedback"]:
                is_assess = (option == "Get Assessment Feedback")
                st.session_state.quiz_questions = generate_quiz_data(selected_tense, api_key, is_assessment=is_assess)
                st.session_state.quiz_active = True
                st.session_state.current_view = "quiz"

# --- UI RENDERING ---
if st.session_state.current_view == "concept" and not st.session_state.quiz_active:
    st.markdown("---")
    sections = st.session_state.explanation_sections
    c_idx = st.session_state.current_card_idx
    titles = ["🃏 Card 1: The Core Blueprint", "📐 Card 2: The Core Formula", "🚦 Card 3: Signals & Triggers"]
    if sections and c_idx < len(sections):
        st.write(f"### {titles[c_idx]}")
        st.info(sections[c_idx])
        col1, col2 = st.columns(2)
        with col1:
            if c_idx > 0 and st.button("⬅️ Previous"): st.session_state.current_card_idx -= 1; st.rerun()
        with col2:
            if c_idx < len(sections) - 1:
                if st.button("Next ➡️"): st.session_state.current_card_idx += 1; st.rerun()
            elif st.button("Finish 🎉"): st.session_state.current_view = None; st.rerun()

if st.session_state.current_view == "examples" and not st.session_state.quiz_active:
    st.markdown("---")
    st.markdown(st.session_state.examples_text)

if st.session_state.quiz_active and st.session_state.quiz_questions:
    st.markdown("---")
    idx = st.session_state.current_question_idx
    qs = st.session_state.quiz_questions
    if idx < len(qs):
        st.write(f"### 📝 Question {idx + 1} of {len(qs)}")
        st.markdown(f"**{qs[idx]['question']}**")
        choice = st.radio("Answer:", qs[idx]["options"], key=f"q_{idx}")
        if not st.session_state.quiz_submitted and st.button("Submit Answer"):
            st.session_state.quiz_submitted = True; st.rerun()
        if st.session_state.quiz_submitted:
            correct = qs[idx]["correct_answer"]
            if choice == correct:
                st.success("🎉 Correct!")
                if f"sc_{idx}" not in st.session_state: st.session_state.score += 1; st.session_state[f"sc_{idx}"] = True
            else:
                st.error(f"❌ Incorrect. Answer: {correct}")
                if f"log_{idx}" not in st.session_state:
                    st.session_state.wrong_answers_history.append({"question": qs[idx]["question"], "user_answer": choice, "correct_answer": correct, "tense_category": qs[idx].get("tense_category", "Unknown")})
                    st.session_state[f"log_{idx}"] = True
            st.info(f"💡 **Explanation:** {qs[idx]['explanation']}")
            if st.button("Next Question ➡️"): st.session_state.current_question_idx += 1; st.session_state.quiz_submitted = False; st.rerun()
    else:
        st.balloons()
        st.markdown(f"### 🏆 Session Complete! Score: **{st.session_state.score}/{len(qs)}**")
        if not st.session_state.macro_feedback:
            with st.spinner("Compiling report..."):
                st.session_state.macro_feedback = generate_macro_feedback(selected_tense, st.session_state.score, len(qs), st.session_state.wrong_answers_history, api_key, is_assessment=(option == "Take Assessment and Get Feedback"))
        st.markdown("### 📊 Twig's Diagnostic Feedback")
        st.markdown(st.session_state.macro_feedback)
        if st.button("Clear Space"):
            for k in ["quiz_active", "quiz_questions", "current_view", "macro_feedback", "wrong_answers_history", "current_question_idx", "score", "quiz_submitted"]:
                st.session_state[k] = [] if isinstance(st.session_state[k], list) else (0 if isinstance(st.session_state[k], int) else (False if isinstance(st.session_state[k], bool) else None))
            st.rerun()