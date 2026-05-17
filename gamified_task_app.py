import streamlit as st
import google.generativeai as genai
import json
import uuid
import os

STATE_FILE = "gamified_state.json"

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
                            "last_eval": None
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
    st.rerun()

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
                    "last_eval": None
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

    # AI Chatbox for Priority Advice
    with col_chat:
        st.header("🤖 AI Advisor")
        st.write("Ask for advice on managing your tasks.")

        # Display chat history
        chat_container = st.container(height=500)
        with chat_container:
            for msg in st.session_state.app_state["chat_history"]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("e.g., Help me prioritize these tasks"):
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

                                # Construct context from current tasks
                                task_context = "Current Tasks:\n"
                                for t in st.session_state.app_state["tasks"]:
                                    task_context += f"- Objective: {t['objective']} (Progress: {t['progress']}%)\n"

                                full_prompt = f"You are a gamified task system AI advisor. Answer the user's query briefly based on their current tasks.\n\n{task_context}\n\nUser Query: {prompt}"

                                response = model.generate_content(full_prompt)
                                response_text = response.text

                                st.markdown(response_text)
                                st.session_state.app_state["chat_history"].append({"role": "assistant", "content": response_text})
                                persist_state()
                            except Exception as e:
                                st.error(f"Error connecting to AI: {e}")

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

        col_report, col_todo = st.columns([1.5, 1])

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
