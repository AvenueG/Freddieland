import streamlit as st
import google.generativeai as genai
import json
import uuid
import os

STATE_FILE = "gamified_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"todo_list": [], "task_objective": "", "current_progress": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

st.set_page_config(page_title="Gamified Task System Engine", page_icon="🎮")

# Load persistent state
app_state = load_state()

# Initialize session state from persistent state
if "todo_list" not in st.session_state:
    st.session_state.todo_list = app_state.get("todo_list", [])
if "task_objective" not in st.session_state:
    st.session_state.task_objective = app_state.get("task_objective", "")
if "current_progress" not in st.session_state:
    st.session_state.current_progress = app_state.get("current_progress", 0)

st.title("🎮 Gamified Task System Engine")
st.write("An objective AI engine that evaluates your daily actions and quantifies your contribution.")

st.header("📋 Current To-Do List")
with st.container():
    if not st.session_state.todo_list:
        st.write("Your to-do list is empty. Add tasks manually or get suggestions from the AI engine!")
    else:
        for idx, task in enumerate(st.session_state.todo_list):
            cols = st.columns([0.8, 0.2])
            with cols[0]:
                is_done = st.checkbox(task["text"], value=task["done"], key=f"todo_{task['id']}")
                # Update task status if changed
                if is_done != task["done"]:
                    st.session_state.todo_list[idx]["done"] = is_done
                    save_state({"todo_list": st.session_state.todo_list, "task_objective": st.session_state.task_objective, "current_progress": st.session_state.current_progress})
            with cols[1]:
                if st.button("Delete", key=f"del_{task['id']}"):
                    st.session_state.todo_list.pop(idx)
                    save_state({"todo_list": st.session_state.todo_list, "task_objective": st.session_state.task_objective, "current_progress": st.session_state.current_progress})
                    st.rerun()

    with st.form("add_todo_form", clear_on_submit=True):
        new_todo = st.text_input("Add a new task...")
        submitted = st.form_submit_button("Add Task")
        if submitted and new_todo.strip():
            st.session_state.todo_list.append({"id": uuid.uuid4().hex, "text": new_todo.strip(), "done": False})
            save_state({"todo_list": st.session_state.todo_list, "task_objective": st.session_state.task_objective, "current_progress": st.session_state.current_progress})
            st.rerun()

st.markdown("---")

with st.sidebar:
    st.header("⚙️ Configuration")
    gemini_api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("---")
    st.markdown("""
    ### Evaluation Rules:
    - **Contribution**: Strict evaluation of daily action against the task objective.
    - **EXP**: 1% contribution = 10 EXP.
    - **Next Step**: Direct, actionable next step based on updated progress.
    """)

st.header("📝 Daily Report")

def update_objective():
    st.session_state.task_objective = st.session_state._task_objective
    save_state({"todo_list": st.session_state.todo_list, "task_objective": st.session_state.task_objective, "current_progress": st.session_state.current_progress})

def update_progress():
    st.session_state.current_progress = st.session_state._current_progress
    save_state({"todo_list": st.session_state.todo_list, "task_objective": st.session_state.task_objective, "current_progress": st.session_state.current_progress})

task_objective = st.text_area(
    "【任务名称与目标】(Task Objective)",
    value=st.session_state.task_objective,
    key="_task_objective",
    on_change=update_objective,
    placeholder="e.g., Complete the frontend design for the new app."
)

# Use _current_progress as the source of truth for the widget
if "_current_progress" not in st.session_state:
    st.session_state._current_progress = st.session_state.current_progress

current_progress = st.number_input(
    "【当前总进度】(Current Progress, %)",
    min_value=0,
    max_value=100,
    value=st.session_state._current_progress,
    key="_current_progress",
    on_change=update_progress
)

daily_action = st.text_area("【今日行动记录】(Daily Action)", placeholder="e.g., Designed the login and registration pages.")

if st.button("Evaluate Action", type="primary"):
    if not gemini_api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not task_objective or not daily_action:
        st.warning("Please fill in both Task Objective and Daily Action.")
    else:
        with st.spinner("Evaluating your progress..."):
            try:
                genai.configure(api_key=gemini_api_key)
                # Use gemini-flash-latest as requested
                model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})

                prompt = f"""
你是一个客观且硬核的“游戏化任务系统”AI引擎。你的职责是评估用户的每日行动，量化其对任务总目标的真实贡献，并提供下一步的战略建议。

# Input
【任务名称与目标】: {task_objective}
【当前总进度】: {current_progress}%
【今日行动记录】: {daily_action}

# Evaluation Rules
1. 真实贡献量化 (Contribution)： 严格评估【今日行动】对【任务目标】的实质性推进。不要奉承用户，如果行动无关紧要或偏离目标，贡献度可以是 0%。
2. 经验值 (EXP) 换算： 贡献度 1% = 10 EXP。
3. 下一步 (Next Step)： 基于更新后的进度，给出直接、可执行的具体下一步动作。

# Output Format
请务必严格按照以下 JSON 格式输出，方便系统解析，不要输出任何除此之外的说明文字：
{{
  "feedback": "客观简短的行动点评（20字以内，例如：‘资料搜集详实，但缺乏核心结论’）",
  "contribution_percent": 增加的进度百分比（仅数字，例如：5）,
  "exp_earned": 获得的经验值（仅数字，例如：50）,
  "new_total_progress": 更新后的总进度百分比（仅数字）,
  "next_step": "下一步具体行动建议（50字以内）"
}}
"""
                response = model.generate_content(prompt)

                try:
                    result = json.loads(response.text)

                    st.success("Evaluation Complete!")

                    new_progress = result.get('new_total_progress', current_progress)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(label="Contribution", value=f"+{result.get('contribution_percent', 0)}%")
                    with col2:
                        st.metric(label="EXP Earned", value=f"+{result.get('exp_earned', 0)}")
                    with col3:
                        st.metric(label="New Total Progress", value=f"{new_progress}%")

                    # Update session state and widget state with the new progress
                    if new_progress != current_progress:
                        st.session_state.current_progress = new_progress
                        st.session_state._current_progress = new_progress
                        save_state({"todo_list": st.session_state.todo_list, "task_objective": st.session_state.task_objective, "current_progress": st.session_state.current_progress})

                    st.info(f"**Feedback:** {result.get('feedback', '')}")

                    next_step = result.get('next_step', '')
                    st.warning(f"**Next Step:** {next_step}")

                    if next_step:
                        st.session_state.todo_list.append({"id": uuid.uuid4().hex, "text": f"[AI Suggestion] {next_step}", "done": False})
                        save_state({"todo_list": st.session_state.todo_list, "task_objective": st.session_state.task_objective, "current_progress": st.session_state.current_progress})
                        st.success("✨ Added next step to your To-Do list!")

                except json.JSONDecodeError:
                    st.error("Failed to parse the response from the AI engine. Please try again.")
                    with st.expander("Raw Response"):
                        st.write(response.text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
