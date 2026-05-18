import streamlit as st
import google.generativeai as genai
import json
import uuid
import os
import re

STATE_FILE = "gamified_state.json"

from datetime import datetime

# --------------------------------------------------------------------------------
# TRANSLATIONS
# --------------------------------------------------------------------------------
TRANSLATIONS = {
    "English": {
        "app_title": "🎮 Gamified Task Dashboard",
        "app_desc": "Manage your goals, sort their priority, and let AI evaluate your daily contributions.",
        "config_header": "⚙️ Configuration",
        "api_key_label": "Gemini API Key",
        "language_label": "Language",
        "eval_rules_title": "### Evaluation Rules:",
        "eval_rules_1": "- **Contribution**: AI determines your daily % contribution. It adds up!",
        "eval_rules_2": "- **EXP**: 1% contribution = 10 EXP.",
        "eval_rules_3": "- **Next Step**: AI updates your To-Do list with actionable advice.",
        "your_goals": "🎯 Your Goals",
        "start_quest": "Start a New Quest",
        "goal_objective": "Goal Objective",
        "goal_placeholder": "e.g., Build a personal portfolio website",
        "add_goal_btn": "Add Goal",
        "no_goals": "No active goals found. Start a new quest above!",
        "completion": "Completion: {}%",
        "enter_quest": "Enter Quest",
        "move_up": "Move Priority Up",
        "move_down": "Move Priority Down",
        "ai_advisor": "🤖 AI Advisor",
        "ai_desc_home": "Ask for advice on managing your tasks.",
        "ai_desc_task": "Ask AI about: {}",
        "apply_sorting": "✨ Apply AI Sorting",
        "tasks_reordered": "Tasks reordered!",
        "ask_question": "Ask a question...",
        "api_key_error": "Please enter your Gemini API Key in the sidebar first.",
        "thinking": "Thinking...",
        "ai_error": "Error connecting to AI: {}",
        "refresh_apply": "🔄 Refresh or scroll up to click the button to apply the sorting!",
        "calendar_title": "📅 Daily Contribution Calendar",
        "calendar_desc": "Your total daily progress contributions across all goals.",
        "no_history": "No contribution history yet. Submit a daily action to see it here!",
        "task_not_found": "Task not found.",
        "back_home": "⬅️ Back to Dashboard",
        "quest_title": "Quest: {}",
        "total_progress": "Total Progress: {}%",
        "submit_action": "📝 Submit Daily Action",
        "action_desc": "What did you accomplish today?",
        "action_placeholder": "e.g., Read 5 pages of the book.",
        "eval_btn": "Evaluate Contribution",
        "action_warning": "Please enter your daily action.",
        "ai_evaluating": "AI is evaluating your contribution...",
        "folder_title": "📂 Folders",
        "folder_all": "All",
        "folder_ongoing": "Ongoing",
        "folder_unfinished": "Unfinished",
        "folder_on_hold": "On Hold",
        "folder_deleted": "Deleted",
        "status_label": "Status",
        "roadmap_title": "🗺️ Quest Roadmap",
        "generate_roadmap": "Generate AI Roadmap",
        "generating_roadmap": "AI is plotting your roadmap...",
        "prev_step": "⬅️ Prev Step",
        "next_step": "Next Step ➡️",
        "parse_error": "Failed to parse AI response.",
        "eval_complete": "Evaluation Complete!",
        "contribution": "Contribution",
        "exp_earned": "EXP Earned",
        "feedback": "**Feedback:** {}",
        "suggested_next": "**Suggested Next Step added to To-Do list:** {}",
        "todo_header": "📋 Quest To-Do List",
        "empty_todo": "Your to-do list is empty.",
        "add_new_task": "Add a new task...",
        "add_task_btn": "Add Task",
        "preset_sort": "Help me prioritize these tasks",
        "preset_sort_prompt": "Help me prioritize my current tasks based on importance and progress.",
        "preset_advice": "Give me advice on my goals",
        "preset_advice_prompt": "Please review all my current goals and progress, and give me specific advice."
    },
    "中文": {
        "app_title": "🎮 游戏化任务面板",
        "app_desc": "管理您的目标，对优先级进行排序，并让AI评估您的日常贡献。",
        "config_header": "⚙️ 偏好设置",
        "api_key_label": "Gemini API 密钥",
        "language_label": "语言",
        "eval_rules_title": "### 评估规则：",
        "eval_rules_1": "- **贡献度**：AI会判定您的每日贡献百分比。进度会不断累加！",
        "eval_rules_2": "- **经验值(EXP)**：1% 贡献度 = 10 EXP。",
        "eval_rules_3": "- **下一步**：AI会给出可执行的建议并加入您的待办列表。",
        "your_goals": "🎯 您的目标",
        "start_quest": "开启新任务",
        "goal_objective": "目标名称",
        "goal_placeholder": "例如：建立个人作品集网站",
        "add_goal_btn": "添加目标",
        "no_goals": "未找到活动目标。请在上方开启新任务！",
        "completion": "完成度: {}%",
        "enter_quest": "进入任务",
        "move_up": "提高优先级",
        "move_down": "降低优先级",
        "ai_advisor": "🤖 AI 顾问",
        "ai_desc_home": "寻求有关管理任务的建议。",
        "ai_desc_task": "向AI询问关于：{}",
        "apply_sorting": "✨ 一键应用 AI 排序",
        "tasks_reordered": "任务重新排序成功！",
        "ask_question": "输入您的问题...",
        "api_key_error": "请先在侧边栏输入您的 Gemini API 密钥。",
        "thinking": "思考中...",
        "ai_error": "连接AI时出错：{}",
        "refresh_apply": "🔄 刷新或向上滚动以点击按钮应用排序！",
        "calendar_title": "📅 每日贡献日历",
        "calendar_desc": "您在所有目标上的每日进度贡献总和。",
        "no_history": "暂无贡献记录。提交日常行动后将显示在这里！",
        "task_not_found": "未找到任务。",
        "back_home": "⬅️ 返回控制台",
        "quest_title": "任务：{}",
        "total_progress": "总进度：{}%",
        "submit_action": "📝 提交今日行动",
        "action_desc": "您今天完成了什么？",
        "action_placeholder": "例如：阅读了5页书。",
        "eval_btn": "评估贡献度",
        "action_warning": "请输入您的日常行动。",
        "ai_evaluating": "AI 正在评估您的贡献...",
        "folder_title": "📂 文件夹",
        "folder_all": "全部",
        "folder_ongoing": "进行中",
        "folder_unfinished": "未完成",
        "folder_on_hold": "已搁置",
        "folder_deleted": "已删除",
        "status_label": "状态",
        "roadmap_title": "🗺️ 任务路线图",
        "generate_roadmap": "生成 AI 路线图",
        "generating_roadmap": "AI 正在规划路线图...",
        "prev_step": "⬅️ 上一步",
        "next_step": "下一步 ➡️",
        "parse_error": "无法解析AI响应。",
        "eval_complete": "评估完成！",
        "contribution": "贡献度",
        "exp_earned": "获得经验",
        "feedback": "**反馈：** {}",
        "suggested_next": "**建议的下一步已添加到待办事项：** {}",
        "todo_header": "📋 任务待办清单",
        "empty_todo": "您的待办清单是空的。",
        "add_new_task": "添加新待办事项...",
        "add_task_btn": "添加待办",
        "preset_sort": "帮我排序任务优先级",
        "preset_sort_prompt": "帮我排序当前任务的优先级。请根据重要性和进度合理安排。",
        "preset_advice": "对我目前的目标提供建议",
        "preset_advice_prompt": "请查看我目前的所有目标和进度，并给我一些具体的建议。"
    },
    "ไทย": {
        "app_title": "🎮 แดชบอร์ดภารกิจเกม",
        "app_desc": "จัดการเป้าหมายของคุณ จัดเรียงลำดับความสำคัญ และให้ AI ประเมินผลงานรายวันของคุณ",
        "config_header": "⚙️ การตั้งค่า",
        "api_key_label": "คีย์ Gemini API",
        "language_label": "ภาษา",
        "eval_rules_title": "### กฎการประเมิน:",
        "eval_rules_1": "- **ผลงาน**: AI จะประเมิน % ผลงานรายวันของคุณ และจะสะสมไปเรื่อยๆ!",
        "eval_rules_2": "- **EXP**: ผลงาน 1% = 10 EXP",
        "eval_rules_3": "- **ขั้นตอนต่อไป**: AI จะอัปเดตรายการที่ต้องทำของคุณด้วยคำแนะนำที่นำไปปฏิบัติได้",
        "your_goals": "🎯 เป้าหมายของคุณ",
        "start_quest": "เริ่มภารกิจใหม่",
        "goal_objective": "วัตถุประสงค์",
        "goal_placeholder": "เช่น สร้างเว็บไซต์พอร์ตโฟลิโอส่วนตัว",
        "add_goal_btn": "เพิ่มเป้าหมาย",
        "no_goals": "ไม่พบเป้าหมายที่ใช้งานอยู่ เริ่มภารกิจใหม่ด้านบนเลย!",
        "completion": "ความสำเร็จ: {}%",
        "enter_quest": "เข้าสู่ภารกิจ",
        "move_up": "เลื่อนความสำคัญขึ้น",
        "move_down": "เลื่อนความสำคัญลง",
        "ai_advisor": "🤖 ที่ปรึกษา AI",
        "ai_desc_home": "ขอคำแนะนำเกี่ยวกับการจัดการงานของคุณ",
        "ai_desc_task": "ถาม AI เกี่ยวกับ: {}",
        "apply_sorting": "✨ ใช้การเรียงลำดับของ AI",
        "tasks_reordered": "จัดเรียงงานใหม่แล้ว!",
        "ask_question": "ถามคำถาม...",
        "api_key_error": "โปรดป้อนคีย์ Gemini API ของคุณที่แถบด้านข้างก่อน",
        "thinking": "กำลังคิด...",
        "ai_error": "เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI: {}",
        "refresh_apply": "🔄 รีเฟรชหรือเลื่อนขึ้นเพื่อคลิกปุ่มเพื่อใช้การเรียงลำดับ!",
        "calendar_title": "📅 ปฏิทินผลงานประจำวัน",
        "calendar_desc": "ผลงานความคืบหน้ารายวันทั้งหมดของคุณในทุกเป้าหมาย",
        "no_history": "ยังไม่มีประวัติผลงาน ส่งการกระทำรายวันเพื่อดูที่นี่!",
        "task_not_found": "ไม่พบงาน",
        "back_home": "⬅️ กลับไปที่แดชบอร์ด",
        "quest_title": "ภารกิจ: {}",
        "total_progress": "ความคืบหน้ารวม: {}%",
        "submit_action": "📝 ส่งการกระทำรายวัน",
        "action_desc": "วันนี้คุณทำอะไรสำเร็จบ้าง?",
        "action_placeholder": "เช่น อ่านหนังสือ 5 หน้า",
        "eval_btn": "ประเมินผลงาน",
        "action_warning": "โปรดป้อนการกระทำรายวันของคุณ",
        "ai_evaluating": "AI กำลังประเมินผลงานของคุณ...",
        "folder_title": "📂 โฟลเดอร์",
        "folder_all": "ทั้งหมด",
        "folder_ongoing": "กำลังดำเนินการ",
        "folder_unfinished": "ยังไม่เสร็จ",
        "folder_on_hold": "ระงับไว้",
        "folder_deleted": "ลบแล้ว",
        "status_label": "สถานะ",
        "roadmap_title": "🗺️ แผนงานภารกิจ",
        "generate_roadmap": "สร้างแผนงาน AI",
        "generating_roadmap": "AI กำลังวางแผนงานของคุณ...",
        "prev_step": "⬅️ ขั้นตอนก่อนหน้า",
        "next_step": "ขั้นตอนถัดไป ➡️",
        "parse_error": "ไม่สามารถแยกวิเคราะห์การตอบสนองของ AI",
        "eval_complete": "การประเมินเสร็จสมบูรณ์!",
        "contribution": "ผลงาน",
        "exp_earned": "EXP ที่ได้รับ",
        "feedback": "**ข้อเสนอแนะ:** {}",
        "suggested_next": "**ขั้นตอนถัดไปที่แนะนำถูกเพิ่มลงในรายการสิ่งที่ต้องทำ:** {}",
        "todo_header": "📋 รายการสิ่งที่ต้องทำของภารกิจ",
        "empty_todo": "รายการสิ่งที่ต้องทำของคุณว่างเปล่า",
        "add_new_task": "เพิ่มงานใหม่...",
        "add_task_btn": "เพิ่มงาน",
        "preset_sort": "ช่วยฉันจัดลำดับความสำคัญของงาน",
        "preset_sort_prompt": "ช่วยฉันจัดลำดับความสำคัญของงานปัจจุบันตามความสำคัญและความคืบหน้า",
        "preset_advice": "ให้คำแนะนำเกี่ยวกับเป้าหมายของฉัน",
        "preset_advice_prompt": "โปรดทบทวนเป้าหมายและความคืบหน้าปัจจุบันของฉันทั้งหมด และให้คำแนะนำที่เจาะจง"
    }
}

def load_state():
    # Define default modern state
    default_state = {
        "api_key": "",
        "language": "English",
        "tasks": [],
        "chat_history": [],
        "total_exp": 0,
        "level": 1,
        "action_history": []
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

                # Ensure existing tasks have contribution_history, recommended_questions, status, and roadmap
                for task in data.get("tasks", []):
                    if "contribution_history" not in task:
                        task["contribution_history"] = []
                    if "recommended_questions" not in task:
                        task["recommended_questions"] = []
                    if "status" not in task:
                        task["status"] = "ongoing"
                    if "roadmap" not in task:
                        task["roadmap"] = {"steps": [], "current_step_index": 0}
                return data
        except Exception:
            pass
    return default_state

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

st.set_page_config(page_title="Gamified Task System Engine", page_icon="🎮", layout="wide")

# Inject Custom iOS-style CSS
st.markdown("""
<style>
    /* Soft background color for the entire app */
    .stApp {
        background-color: #f4f5f7;
    }

    /* Rounded containers with subtle shadows to look like iOS cards */
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: none;
        margin-bottom: 12px;
    }

    /* Style the main column slightly differently if needed */
    div[data-testid="stColumn"] {
        padding: 10px;
    }

    /* Modern, sleek rounded inputs */
    input[type="text"], textarea, input[type="password"] {
        border-radius: 12px !important;
        border: 1px solid #d1d5db !important;
        padding: 10px 14px !important;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.05) !important;
        transition: all 0.2s ease-in-out !important;
    }

    input[type="text"]:focus, textarea:focus, input[type="password"]:focus {
        border-color: #007aff !important;
        box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.2) !important;
    }

    /* Primary Buttons - iOS Blue style */
    button[kind="primary"] {
        background-color: #007aff !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0, 122, 255, 0.3) !important;
        transition: all 0.2s ease !important;
    }

    button[kind="primary"]:hover {
        background-color: #005bb5 !important;
        box-shadow: 0 4px 8px rgba(0, 122, 255, 0.4) !important;
        transform: translateY(-1px);
    }

    /* Secondary Buttons - Light gray */
    button[kind="secondary"] {
        background-color: #f1f3f5 !important;
        color: #333 !important;
        border-radius: 12px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        border: 1px solid #e5e7eb !important;
        transition: all 0.2s ease !important;
    }

    button[kind="secondary"]:hover {
        background-color: #e2e6ea !important;
        transform: translateY(-1px);
    }

    /* Progress Bars */
    .stProgress > div > div > div > div {
        background-color: #34c759;
        border-radius: 10px;
    }
    .stProgress > div > div {
        background-color: #e5e5ea;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

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

def get_gamer_title(level):
    if level < 5:
        return "Novice"
    elif level < 15:
        return "Grinder"
    elif level < 30:
        return "Veteran"
    elif level < 50:
        return "Master"
    else:
        return "Legend"

def render_level_header():
    total_exp = st.session_state.app_state.get("total_exp", 0)
    level = st.session_state.app_state.get("level", 1)
    title = get_gamer_title(level)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gamer Title", title)
    with col2:
        st.metric("Level", level)
    with col3:
        st.metric("Total EXP", total_exp)
    st.markdown("---")

def t(key, *args):
    lang = st.session_state.app_state.get("language", "English")
    if lang not in TRANSLATIONS:
        lang = "English"
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["English"].get(key, key))
    if args:
        return text.format(*args)
    return text

def render_ai_chatbox(context_type, context_data, custom_presets=None):
    st.header(t("ai_advisor"))
    if context_type == "dashboard":
        st.write(t("ai_desc_home"))
    else:
        st.write(t("ai_desc_task", context_data.get('objective', '')))

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
                        if st.button(t("apply_sorting"), key=f"apply_sort_{idx}"):
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
                            st.success(t("tasks_reordered"))
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
    prompt = st.chat_input(t("ask_question"))
    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None

    if prompt:
        if not st.session_state.app_state["api_key"]:
            st.error(t("api_key_error"))
        else:
            st.session_state.app_state["chat_history"].append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner(t("thinking")):
                        try:
                            genai.configure(api_key=st.session_state.app_state["api_key"])
                            model = genai.GenerativeModel('gemini-flash-latest')

                            lang = st.session_state.app_state.get("language", "English")
                            system_instruction = ""
                            if context_type == "dashboard":
                                task_context = "Current Tasks:\n"
                                for task_item in context_data:
                                    task_context += f"- ID: {task_item['id']} | Objective: {task_item['objective']} | Progress: {task_item['progress']}%\n"

                                system_instruction = f"""
You are a gamified task system AI advisor. Answer the user's query briefly based on their current tasks. YOU MUST RESPOND IN {lang}.

IF the user asks to SORT or PRIORITIZE tasks, you MUST provide a friendly explanation of your reasoning in {lang}, AND append a strict JSON block at the very end of your response exactly like this:
```json
{{
  "action": "reorder",
  "new_order": ["<task_id_1>", "<task_id_2>"]
}}
```
Include ALL task IDs in the new order, from most important to least important. Do not output this JSON block unless prioritizing.
"""
                            elif context_type == "task_detail":
                                task_context = f"Current Task: {context_data['objective']}\nCurrent Progress: {context_data['progress']}%"
                                system_instruction = f"You are a helpful AI advisor focused on helping the user accomplish the specific task provided. Answer their questions directly, creatively, and briefly. YOU MUST RESPOND IN {lang}."

                            full_prompt = f"{system_instruction}\n\n{task_context}\n\nUser Query: {prompt}"

                            response = model.generate_content(full_prompt)
                            response_text = response.text

                            # Clean JSON if it exists (only relevant for dashboard sorting)
                            match = re.search(r'```json\s*\n(\{\s*"action"\s*:\s*"reorder"[\s\S]*?\})\s*\n```', response_text)
                            if match and context_type == "dashboard":
                                clean_text = response_text[:match.start()] + response_text[match.end():]
                                st.markdown(clean_text)
                                st.info(t("refresh_apply"))
                            else:
                                st.markdown(response_text)

                            st.session_state.app_state["chat_history"].append({"role": "assistant", "content": response_text})
                            persist_state()
                            st.rerun()
                        except Exception as e:
                            st.error(t("ai_error", e))

def render_calendar(tasks):
    with st.expander(t("calendar_title"), expanded=False):
        st.write(t("calendar_desc"))
        # Aggregate history
        history = {}
        for task_item in tasks:
            for record in task_item.get("contribution_history", []):
                date = record["date"]
                if date not in history:
                    history[date] = []
                history[date].append(f"[{task_item['objective']}]: +{record['contribution']}% - {record['action']}")

        if not history:
            st.info(t("no_history"))
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
    st.title(t("app_title"))
    render_level_header()
    st.write(t("app_desc"))

    # Sidebar: API Key Configuration & Language & Folders
    with st.sidebar:
        st.header(t("folder_title"))
        folder_options = [
            ("all", t("folder_all")),
            ("ongoing", t("folder_ongoing")),
            ("unfinished", t("folder_unfinished")),
            ("on_hold", t("folder_on_hold")),
            ("deleted", t("folder_deleted"))
        ]

        selected_folder = st.radio(
            "Select Folder",
            options=[x[0] for x in folder_options],
            format_func=lambda x: next(item[1] for item in folder_options if item[0] == x),
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.header(t("config_header"))

        langs = ["English", "中文", "ไทย"]
        curr_lang = st.session_state.app_state.get("language", "English")
        curr_lang_idx = langs.index(curr_lang) if curr_lang in langs else 0
        new_lang = st.selectbox(t("language_label"), langs, index=curr_lang_idx)
        if new_lang != curr_lang:
            st.session_state.app_state["language"] = new_lang
            persist_state()
            st.rerun()

        new_api_key = st.text_input(t("api_key_label"), value=st.session_state.app_state["api_key"], type="password")
        if new_api_key != st.session_state.app_state["api_key"]:
            st.session_state.app_state["api_key"] = new_api_key
            persist_state()

        st.markdown("---")
        st.markdown(f"""
        {t("eval_rules_title")}
        {t("eval_rules_1")}
        {t("eval_rules_2")}
        {t("eval_rules_3")}
        """)

    col_main, col_chat = st.columns([2, 1])

    with col_main:
        st.header(t("your_goals"))

        # Form to add a new task
        with st.form("add_task_form", clear_on_submit=True):
            st.subheader(t("start_quest"))
            new_task_objective = st.text_input(t("goal_objective"), placeholder=t("goal_placeholder"))
            col_add, _ = st.columns([1, 4])
            with col_add:
                submit_task = st.form_submit_button(t("add_goal_btn"))

            if submit_task and new_task_objective.strip():
                st.session_state.app_state["tasks"].insert(0, {
                    "id": uuid.uuid4().hex,
                    "objective": new_task_objective.strip(),
                    "progress": 0,
                    "todo_list": [],
                    "last_eval": None,
                    "contribution_history": [],
                    "recommended_questions": [],
                    "status": "ongoing",
                    "roadmap": {"steps": [], "current_step_index": 0}
                })
                persist_state()
                st.rerun()

        st.markdown("---")

        tasks = st.session_state.app_state["tasks"]

        # Filter tasks by folder
        if selected_folder == "all":
            filtered_tasks = [t_obj for t_obj in tasks if t_obj.get("status") != "deleted"]
        else:
            filtered_tasks = [t_obj for t_obj in tasks if t_obj.get("status") == selected_folder]

        if not filtered_tasks:
            st.info(t("no_goals"))
        else:
            # Display tasks with manual sorting (Move Up/Down)
            for i, task in enumerate(filtered_tasks):
                # Find original index for sorting logic
                orig_i = tasks.index(task)

                with st.container(border=True):
                    col_info, col_actions = st.columns([2.5, 1.5])
                    with col_info:
                        st.subheader(task["objective"])
                        st.progress(task["progress"] / 100.0, text=t("completion", task['progress']))
                    with col_actions:
                        # Status dropdown
                        status_opts = ["ongoing", "unfinished", "on_hold", "deleted"]
                        current_status = task.get("status", "ongoing")
                        curr_idx = status_opts.index(current_status) if current_status in status_opts else 0

                        new_status = st.selectbox(
                            t("status_label"),
                            options=status_opts,
                            index=curr_idx,
                            format_func=lambda x: t(f"folder_{x}"),
                            key=f"status_{task['id']}",
                            label_visibility="collapsed"
                        )
                        if new_status != current_status:
                            tasks[orig_i]["status"] = new_status
                            persist_state()
                            st.rerun()

                        action_cols = st.columns(3)
                        with action_cols[0]:
                            if st.button(t("enter_quest"), key=f"enter_{task['id']}", use_container_width=True):
                                navigate_to("task_detail", task["id"])

                        with action_cols[1]:
                            if st.button("⬆️", key=f"up_{task['id']}", disabled=(orig_i == 0), help=t("move_up")):
                                tasks[orig_i], tasks[orig_i-1] = tasks[orig_i-1], tasks[orig_i]
                                persist_state()
                                st.rerun()
                        with action_cols[2]:
                            if st.button("⬇️", key=f"down_{task['id']}", disabled=(orig_i == len(tasks) - 1), help=t("move_down")):
                                tasks[orig_i], tasks[orig_i+1] = tasks[orig_i+1], tasks[orig_i]
                                persist_state()
                                st.rerun()

    with col_main:
        render_calendar(st.session_state.app_state["tasks"])

    with col_chat:
        presets = [
            {"label": t("preset_sort"), "prompt": t("preset_sort_prompt")},
            {"label": t("preset_advice"), "prompt": t("preset_advice_prompt")}
        ]
        render_ai_chatbox("dashboard", st.session_state.app_state["tasks"], presets)

    st.markdown("---")

    with st.expander("📜 Global Action History", expanded=False):
        history = st.session_state.app_state.get("action_history", [])
        if not history:
            st.write("No actions evaluated yet. Complete a task action to see your history here!")
        else:
            for item in reversed(history):
                st.markdown(f"**{item['date']}** - *{item['objective']}*")
                st.markdown(f"> **Action:** {item['action']}")
                st.markdown(f"> **Feedback:** {item['feedback']}")
                st.markdown(f"> 🏅 **+{item['exp_earned']} EXP**")
                st.markdown("---")

# --------------------------------------------------------------------------------
# TASK DETAIL PAGE
# --------------------------------------------------------------------------------
elif st.session_state.current_page == "task_detail":
    # Find current task
    task = next((t for t in st.session_state.app_state["tasks"] if t["id"] == st.session_state.current_task_id), None)

    if not task:
        st.error(t("task_not_found"))
        if st.button(t("back_home")):
            navigate_to("home")
    else:
        st.button(t("back_home"), on_click=lambda: navigate_to("home"))
        render_level_header()
        st.title(t("quest_title", task['objective']))
        st.progress(task["progress"] / 100.0, text=t("total_progress", task['progress']))

        # --------------------------------------------------------------------------------
        # ROADMAP FEATURE
        # --------------------------------------------------------------------------------
        st.markdown("---")
        st.subheader(t("roadmap_title"))

        roadmap = task.get("roadmap", {"steps": [], "current_step_index": 0})

        if not roadmap.get("steps"):
            if st.button(t("generate_roadmap"), type="secondary"):
                if not st.session_state.app_state["api_key"]:
                    st.error(t("api_key_error"))
                else:
                    with st.spinner(t("generating_roadmap")):
                        try:
                            genai.configure(api_key=st.session_state.app_state["api_key"])
                            model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})
                            lang = st.session_state.app_state.get("language", "English")

                            prompt = f"""
                            You are a quest designer. Break down the following objective into a 5-7 step roadmap or skill-tree.
                            Objective: "{task['objective']}"
                            Ensure the response is strictly JSON. The language MUST be {lang}.
                            Format:
                            {{
                                "steps": ["Step 1 Description", "Step 2 Description", ...]
                            }}
                            """
                            response = model.generate_content(prompt)
                            data = json.loads(response.text)
                            if "steps" in data:
                                task["roadmap"] = {"steps": data["steps"], "current_step_index": 0}
                                persist_state()
                                st.rerun()
                        except Exception as e:
                            st.error(t("ai_error", e))
        else:
            steps = roadmap["steps"]
            current_idx = roadmap["current_step_index"]

            # Custom HTML/CSS for a vertical visual timeline
            html_content = "<div style='position:relative; margin-left: 20px; padding-bottom: 20px;'>"
            html_content += "<div style='position:absolute; left: 11px; top: 10px; bottom: 10px; width: 4px; background-color: #e5e7eb; z-radius: 2px;'></div>"

            for i, step in enumerate(steps):
                is_completed = i < current_idx
                is_active = i == current_idx

                if is_completed:
                    color = "#34c759"
                    icon = "✓"
                    text_style = "color: #4b5563; text-decoration: line-through;"
                elif is_active:
                    color = "#007aff"
                    icon = "●"
                    text_style = "color: #111827; font-weight: bold;"
                else:
                    color = "#9ca3af"
                    icon = "○"
                    text_style = "color: #9ca3af;"

                html_content += f"""
                <div style='display: flex; align-items: flex-start; margin-bottom: 20px; position: relative;'>
                    <div style='z-index: 10; margin-top: 2px; width: 26px; height: 26px; border-radius: 50%; background-color: {color}; color: white; display: flex; align-items: center; justify-content: center; font-size: 14px; box-shadow: 0 0 0 4px #ffffff;'>
                        {icon}
                    </div>
                    <div style='margin-left: 15px; padding-top: 4px; {text_style} font-size: 16px;'>
                        {step}
                    </div>
                </div>
                """
            html_content += "</div>"

            st.markdown(html_content, unsafe_allow_html=True)

            ctrl_col1, ctrl_col2, _ = st.columns([1, 1, 3])
            with ctrl_col1:
                if st.button(t("prev_step"), disabled=current_idx == 0):
                    task["roadmap"]["current_step_index"] -= 1
                    persist_state()
                    st.rerun()
            with ctrl_col2:
                if st.button(t("next_step"), disabled=current_idx >= len(steps)):
                    task["roadmap"]["current_step_index"] += 1
                    persist_state()
                    st.rerun()

        st.markdown("---")
        render_calendar(st.session_state.app_state["tasks"])
        st.markdown("---")

        col_report, col_todo, col_chat = st.columns([1.2, 1, 1.2])

        with col_report:
            st.header(t("submit_action"))
            daily_action = st.text_area(t("action_desc"), placeholder=t("action_placeholder"))

            if st.button(t("eval_btn"), type="primary"):
                if not st.session_state.app_state["api_key"]:
                    st.error(t("api_key_error"))
                elif not daily_action.strip():
                    st.warning(t("action_warning"))
                else:
                    with st.spinner(t("ai_evaluating")):
                        try:
                            genai.configure(api_key=st.session_state.app_state["api_key"])
                            model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})

                            lang = st.session_state.app_state.get("language", "English")
                            eval_prompt = f"""
You are an objective gamified task system AI engine. Evaluate the user's daily action and quantify its true contribution to the task objective. YOU MUST RESPOND IN {lang}.

# Input
Task Objective: {task['objective']}
Current Progress: {task['progress']}%
Daily Action: {daily_action}

# Evaluation Rules
1. Contribution: Strictly evaluate the substantive progress made by the action towards the objective. If irrelevant, contribution is 0. If it made progress, give a reasonable positive percentage (e.g., 1 to 5, depending on scale).
2. Next Step: Provide a specific, actionable next step for this task.

# Output Format
Output exactly this JSON format. The 'feedback' and 'next_step' strings must be written in {lang}.
{{
  "feedback": "Objective, short feedback on the action",
  "contribution_percent": 2,
  "next_step": "A specific next step"
}}
"""
                            response = model.generate_content(eval_prompt)

                            try:
                                result = json.loads(response.text)
                                contribution = float(result.get('contribution_percent', 0))

                                # Accumulate progress safely up to 100
                                new_progress = min(100.0, task['progress'] + contribution)

                                # Calculate EXP
                                exp_earned = int(contribution * 10)

                                # Update Global Leveling
                                st.session_state.app_state["total_exp"] += exp_earned
                                st.session_state.app_state["level"] = (st.session_state.app_state["total_exp"] // 100) + 1

                                # Append to Global Action History
                                st.session_state.app_state["action_history"].append({
                                    "objective": task['objective'],
                                    "action": daily_action,
                                    "feedback": result.get('feedback', ''),
                                    "exp_earned": exp_earned,
                                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                                })

                                # Update task state
                                task['progress'] = new_progress
                                task['last_eval'] = {
                                    "feedback": result.get('feedback', ''),
                                    "contribution": contribution,
                                    "exp_earned": exp_earned,
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
                                st.error(t("parse_error"))
                                st.write(response.text)

                        except Exception as e:
                            st.error(t("ai_error", e))

            # Display Last Evaluation Results
            if task.get("last_eval"):
                st.success(t("eval_complete"))
                eval_data = task["last_eval"]

                met1, met2 = st.columns(2)
                with met1:
                    st.metric(t("contribution"), f"+{eval_data['contribution']}%")
                with met2:
                    st.metric(t("exp_earned"), f"+{eval_data['exp_earned']}")

                st.info(t("feedback", eval_data['feedback']))
                st.warning(t("suggested_next", eval_data['next_step']))

        with col_todo:
            st.header(t("todo_header"))
            with st.container(border=True):
                if not task["todo_list"]:
                    st.write(t("empty_todo"))
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
                    new_todo = st.text_input(t("add_new_task"))
                    if st.form_submit_button(t("add_task_btn")) and new_todo.strip():
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
                        lang = st.session_state.app_state.get("language", "English")
                        q_prompt = f"""
Based on the task objective: "{task['objective']}", generate 2 highly relevant and interesting questions the user might want to ask an AI to get more context, history, or actionable advice.
The questions MUST be written in {lang}.
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
