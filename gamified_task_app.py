import streamlit as st
import google.generativeai as genai
import json
import uuid
import os
import re

STATE_FILE = "gamified_state.json"

from datetime import datetime

def load_state():
    # Define default modern state
    default_state = {
        "api_key": "",
        "tasks": [],
        "chat_history": []
    }

    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)

                # Migration logic: if old schema (single task) is detected, migrate it to new schema
                if "task_objective" in data:
                    migrated_state = default_state.copy()
                    if data.get("task_objective"):
                        migrated_state["tasks"].append({
                            "id": uuid.uuid4().hex,
                            "objective": data.get("task_objective", ""),
                            "progress": data.get("current_progress", 0),
                            "todo_list": data.get("todo_list", []),
                            "last_eval": None,
                            "contribution_history": []
                        })
                    return migrated_state

                # Ensure all keys exist if it's already new schema
                for key in default_state:
                    if key not in data:
                        data[key] = default_state[key]
                return data
        except Exception:
            pass
    return default_state

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

st.set_page_config(page_title="Gamified Task System Engine", page_icon="🎮", layout="wide")

# Initialize session state from persistent state
if "app_state" not in st.session_state:
    st.session_state.app_state = load_state()

# Helper function to persist state
def persist_state():
    save_state(st.session_state.app_state)

# Initialize navigation state
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None

def navigate_to(page, task_id=None):
    st.session_state.current_page = page
    st.session_state.current_task_id = task_id
    # Clear chat history when switching contexts to avoid confusion
    st.session_state.app_state["chat_history"] = []
    persist_state()
    st.rerun()

def render_ai_chatbox(context_type, context_data, custom_presets=None):
    st.header("🤖 AI Advisor")
    if context_type == "dashboard":
        st.write("Ask for advice on managing your tasks.")
    else:
        st.write(f"Ask AI about: {context_data.get('objective', 'this task')}")

    # Display chat history
    chat_container = st.container(height=450)
    with chat_container:
        for idx, msg in enumerate(st.session_state.app_state["chat_history"]):
            with st.chat_message(msg["role"]):
                content = msg["content"]

                # Look for hidden JSON reorder block
                match = re.search(r'```json\s*\n(\{\s*"action"\s*:\s*"reorder"[\s\S]*?\})\s*\n```', content)
                if match and context_type == "dashboard":
                    try:
                        reorder_data = json.loads(match.group(1))
                        clean_text = content[:match.start()] + content[match.end():]
                        st.markdown(clean_text)

                        # Interactive Action Button
                        if st.button("✨ 一键应用 AI 排序 (Apply Sorting)", key=f"apply_sort_{idx}"):
                            new_order_ids = reorder_data.get("new_order", [])
                            task_dict = {t["id"]: t for t in st.session_state.app_state["tasks"]}
                            reordered_tasks = []
                            # Add in the new order
                            for tid in new_order_ids:
                                if tid in task_dict:
                                    reordered_tasks.append(task_dict.pop(tid))
                            # Add any remaining tasks that the AI missed
                            reordered_tasks.extend(task_dict.values())
                            st.session_state.app_state["tasks"] = reordered_tasks
                            persist_state()
                            st.success("Tasks reordered!")
                            st.rerun()

                    except json.JSONDecodeError:
                        st.markdown(content)
                else:
                    st.markdown(content)

    # Preset action buttons
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None

    if custom_presets:
        cols = st.columns(len(custom_presets))
        for i, preset in enumerate(custom_presets):
            with cols[i]:
                if st.button(preset["label"], use_container_width=True):
                    st.session_state.pending_prompt = preset["prompt"]

    # Handle chat input or preset click
    prompt = st.chat_input("Ask a question...")
    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None

    if prompt:
        if not st.session_state.app_state["api_key"]:
            st.error("Please enter your Gemini API Key in the sidebar first.")
        else:
            st.session_state.app_state["chat_history"].append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            genai.configure(api_key=st.session_state.app_state["api_key"])
                            model = genai.GenerativeModel('gemini-flash-latest')

                            system_instruction = ""
                            if context_type == "dashboard":
                                task_context = "Current Tasks:\n"
                                for t in context_data:
                                    task_context += f"- ID: {t['id']} | Objective: {t['objective']} | Progress: {t['progress']}%\n"

                                system_instruction = """
You are a gamified task system AI advisor. Answer the user's query briefly based on their current tasks.

IF the user asks to SORT or PRIORITIZE tasks, you MUST provide a friendly explanation of your reasoning, AND append a strict JSON block at the very end of your response exactly like this:
```json
{
  "action": "reorder",
  "new_order": ["<task_id_1>", "<task_id_2>"]
}
```
Include ALL task IDs in the new order, from most important to least important. Do not output this JSON block unless prioritizing.
"""
                            elif context_type == "task_detail":
                                task_context = f"Current Task: {context_data['objective']}\nCurrent Progress: {context_data['progress']}%"
                                system_instruction = "You are a helpful AI advisor focused on helping the user accomplish the specific task provided. Answer their questions directly, creatively, and briefly."

                            full_prompt = f"{system_instruction}\n\n{task_context}\n\nUser Query: {prompt}"

                            response = model.generate_content(full_prompt)
                            response_text = response.text

                            # Clean JSON if it exists (only relevant for dashboard sorting)
                            match = re.search(r'```json\s*\n(\{\s*"action"\s*:\s*"reorder"[\s\S]*?\})\s*\n```', response_text)
                            if match and context_type == "dashboard":
                                clean_text = response_text[:match.start()] + response_text[match.end():]
                                st.markdown(clean_text)
                                st.info("🔄 Refresh or scroll up to click the button to apply the sorting!")
                            else:
                                st.markdown(response_text)

                            st.session_state.app_state["chat_history"].append({"role": "assistant", "content": response_text})
                            persist_state()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error connecting to AI: {e}")

def render_calendar(tasks):
    with st.expander("📅 Daily Contribution Calendar", expanded=False):
        st.write("Your total daily progress contributions across all goals.")
        # Aggregate history
        history = {}
        for t in tasks:
            for record in t.get("contribution_history", []):
                date = record["date"]
                if date not in history:
                    history[date] = []
                history[date].append(f"[{t['objective']}]: +{record['contribution']}% - {record['action']}")

        if not history:
            st.info("No contribution history yet. Submit a daily action to see it here!")
        else:
            # Sort dates descending
            for date in sorted(history.keys(), reverse=True):
                st.markdown(f"**{date}**")
                for item in history[date]:
                    st.markdown(f"- {item}")

# --------------------------------------------------------------------------------
# HOME PAGE
# --------------------------------------------------------------------------------
if st.session_state.current_page == "home":
    st.title("🎮 Gamified Task Dashboard")
    st.write("Manage your goals, sort their priority, and let AI evaluate your daily contributions.")

    # Sidebar: API Key Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        new_api_key = st.text_input("Gemini API Key", value=st.session_state.app_state["api_key"], type="password")
        if new_api_key != st.session_state.app_state["api_key"]:
            st.session_state.app_state["api_key"] = new_api_key
            persist_state()

        st.markdown("---")
        st.markdown("""
        ### Evaluation Rules:
        - **Contribution**: AI determines your daily % contribution. It adds up!
        - **EXP**: 1% contribution = 10 EXP.
        - **Next Step**: AI updates your To-Do list with actionable advice.
        """)

    col_main, col_chat = st.columns([2, 1])

    with col_main:
        st.header("🎯 Your Goals")

        # Form to add a new task
        with st.form("add_task_form", clear_on_submit=True):
            st.subheader("Start a New Quest")
            new_task_objective = st.text_input("Goal Objective", placeholder="e.g., Build a personal portfolio website")
            col_add, _ = st.columns([1, 4])
            with col_add:
                submit_task = st.form_submit_button("Add Goal")

            if submit_task and new_task_objective.strip():
                st.session_state.app_state["tasks"].append({
                    "id": uuid.uuid4().hex,
                    "objective": new_task_objective.strip(),
                    "progress": 0,
                    "todo_list": [],
                    "last_eval": None,
                    "contribution_history": [],
                    "recommended_questions": []
                })
                persist_state()
                st.rerun()

        st.markdown("---")

        if not st.session_state.app_state["tasks"]:
            st.info("No active goals found. Start a new quest above!")
        else:
            # Display tasks with manual sorting (Move Up/Down)
            tasks = st.session_state.app_state["tasks"]
            for i, task in enumerate(tasks):
                with st.container(border=True):
                    col_info, col_actions = st.columns([3, 1])
                    with col_info:
                        st.subheader(task["objective"])
                        st.progress(task["progress"] / 100.0, text=f"Completion: {task['progress']}%")
                    with col_actions:
                        if st.button("Enter Quest", key=f"enter_{task['id']}", use_container_width=True):
                            navigate_to("task_detail", task["id"])

                        sort_cols = st.columns(2)
                        with sort_cols[0]:
                            if st.button("⬆️", key=f"up_{task['id']}", disabled=(i == 0), help="Move Priority Up"):
                                tasks[i], tasks[i-1] = tasks[i-1], tasks[i]
                                persist_state()
                                st.rerun()
                        with sort_cols[1]:
                            if st.button("⬇️", key=f"down_{task['id']}", disabled=(i == len(tasks) - 1), help="Move Priority Down"):
                                tasks[i], tasks[i+1] = tasks[i+1], tasks[i]
                                persist_state()
                                st.rerun()

    with col_main:
        render_calendar(st.session_state.app_state["tasks"])

    with col_chat:
        presets = [
            {"label": "帮我排序任务优先级", "prompt": "帮我排序当前任务的优先级。请根据重要性和进度合理安排。"},
            {"label": "对我目前的目标提供建议", "prompt": "请查看我目前的所有目标和进度，并给我一些具体的建议。"}
        ]
        render_ai_chatbox("dashboard", st.session_state.app_state["tasks"], presets)

# --------------------------------------------------------------------------------
# TASK DETAIL PAGE
# --------------------------------------------------------------------------------
elif st.session_state.current_page == "task_detail":
    # Find current task
    task = next((t for t in st.session_state.app_state["tasks"] if t["id"] == st.session_state.current_task_id), None)

    if not task:
        st.error("Task not found.")
        if st.button("Back to Home"):
            navigate_to("home")
    else:
        st.button("⬅️ Back to Dashboard", on_click=lambda: navigate_to("home"))
        st.title(f"Quest: {task['objective']}")
        st.progress(task["progress"] / 100.0, text=f"Total Progress: {task['progress']}%")

        render_calendar(st.session_state.app_state["tasks"])
        st.markdown("---")

        col_report, col_todo, col_chat = st.columns([1.2, 1, 1.2])

        with col_report:
            st.header("📝 Submit Daily Action")
            daily_action = st.text_area("What did you accomplish today?", placeholder="e.g., Read 5 pages of the book.")

            if st.button("Evaluate Contribution", type="primary"):
                if not st.session_state.app_state["api_key"]:
                    st.error("Please configure your Gemini API Key on the Home page.")
                elif not daily_action.strip():
                    st.warning("Please enter your daily action.")
                else:
                    with st.spinner("AI is evaluating your contribution..."):
                        try:
                            genai.configure(api_key=st.session_state.app_state["api_key"])
                            model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})

                            # Updated prompt: AI only returns contribution percent, we handle accumulation
                            eval_prompt = f"""
你是一个客观且硬核的“游戏化任务系统”AI引擎。你的职责是评估用户的每日行动，量化其对任务总目标的真实贡献，并提供下一步的战略建议。

# Input
【任务名称与目标】: {task['objective']}
【当前总进度】: {task['progress']}%
【今日行动记录】: {daily_action}

# Evaluation Rules
1. 真实贡献量化 (Contribution)： 严格评估【今日行动】对【任务目标】的实质性推进。如果行动无关紧要或偏离目标，贡献度可以是 0。如果行动有实质性进展，给出一个合理的正数百分比（例如 1 到 5 等，取决于任务规模和行动力度）。
2. 下一步 (Next Step)： 基于此任务给出具体、可执行的下一步建议。

# Output Format
请务必严格按照以下 JSON 格式输出，不要输出任何除此之外的说明文字：
{{
  "feedback": "客观简短的行动点评（20字以内）",
  "contribution_percent": 增加的进度百分比（仅数字，例如：2）,
  "next_step": "下一步具体行动建议（50字以内）"
}}
"""
                            response = model.generate_content(eval_prompt)

                            try:
                                result = json.loads(response.text)
                                contribution = float(result.get('contribution_percent', 0))

                                # Accumulate progress safely up to 100
                                new_progress = min(100.0, task['progress'] + contribution)

                                # Update task state
                                task['progress'] = new_progress
                                task['last_eval'] = {
                                    "feedback": result.get('feedback', ''),
                                    "contribution": contribution,
                                    "exp_earned": int(contribution * 10),
                                    "next_step": result.get('next_step', '')
                                }

                                if "contribution_history" not in task:
                                    task["contribution_history"] = []

                                today = datetime.now().strftime("%Y-%m-%d")
                                task["contribution_history"].append({
                                    "date": today,
                                    "contribution": contribution,
                                    "action": daily_action
                                })

                                next_step = result.get('next_step', '')
                                if next_step:
                                    task['todo_list'].append({"id": uuid.uuid4().hex, "text": f"[AI Suggestion] {next_step}", "done": False})

                                persist_state()
                                st.rerun()

                            except json.JSONDecodeError:
                                st.error("Failed to parse AI response.")
                                st.write(response.text)

                        except Exception as e:
                            st.error(f"Error evaluating action: {e}")

            # Display Last Evaluation Results
            if task.get("last_eval"):
                st.success("Evaluation Complete!")
                eval_data = task["last_eval"]

                met1, met2 = st.columns(2)
                with met1:
                    st.metric("Contribution", f"+{eval_data['contribution']}%")
                with met2:
                    st.metric("EXP Earned", f"+{eval_data['exp_earned']}")

                st.info(f"**Feedback:** {eval_data['feedback']}")
                st.warning(f"**Suggested Next Step added to To-Do list:** {eval_data['next_step']}")

        with col_todo:
            st.header("📋 Quest To-Do List")
            with st.container(border=True):
                if not task["todo_list"]:
                    st.write("Your to-do list is empty.")
                else:
                    for i, todo in enumerate(task["todo_list"]):
                        t_cols = st.columns([0.8, 0.2])
                        with t_cols[0]:
                            is_done = st.checkbox(todo["text"], value=todo["done"], key=f"todo_{todo['id']}")
                            if is_done != todo["done"]:
                                task["todo_list"][i]["done"] = is_done
                                persist_state()
                        with t_cols[1]:
                            if st.button("❌", key=f"del_{todo['id']}"):
                                task["todo_list"].pop(i)
                                persist_state()
                                st.rerun()

                with st.form("add_todo_form_detail", clear_on_submit=True):
                    new_todo = st.text_input("Add a new task...")
                    if st.form_submit_button("Add Task") and new_todo.strip():
                        task["todo_list"].append({"id": uuid.uuid4().hex, "text": new_todo.strip(), "done": False})
                        persist_state()
                        st.rerun()

        with col_chat:
            # Generate dynamic presets for this specific task if they don't exist
            if "recommended_questions" not in task or not task["recommended_questions"]:
                task["recommended_questions"] = []
                if st.session_state.app_state["api_key"]:
                    try:
                        genai.configure(api_key=st.session_state.app_state["api_key"])
                        model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})
                        q_prompt = f"""
Based on the task objective: "{task['objective']}", generate 2 highly relevant and interesting questions the user might want to ask an AI to get more context, history, or actionable advice.
Output exactly this JSON format:
{{
  "questions": ["Question 1", "Question 2"]
}}
"""
                        resp = model.generate_content(q_prompt)
                        q_data = json.loads(resp.text)
                        task["recommended_questions"] = q_data.get("questions", [])
                        persist_state()
                    except Exception:
                        pass # Silently fail and fallback to default or empty if generation fails

            presets = []
            for q in task.get("recommended_questions", []):
                # Truncate label if too long for a button
                label = q if len(q) < 20 else q[:18] + "..."
                presets.append({"label": label, "prompt": q})

            render_ai_chatbox("task_detail", task, presets)
