import streamlit as st
import google.generativeai as genai
import json

st.set_page_config(page_title="Gamified Task System Engine", page_icon="🎮")

st.title("🎮 Gamified Task System Engine")
st.write("An objective AI engine that evaluates your daily actions and quantifies your contribution.")

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

task_objective = st.text_area("【任务名称与目标】(Task Objective)", placeholder="e.g., Complete the frontend design for the new app.")
current_progress = st.number_input("【当前总进度】(Current Progress, %)", min_value=0, max_value=100, value=0)
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
                # Use gemini-1.5-flash as it is fast and supports JSON response format
                model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"response_mime_type": "application/json"})

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

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(label="Contribution", value=f"+{result.get('contribution_percent', 0)}%")
                    with col2:
                        st.metric(label="EXP Earned", value=f"+{result.get('exp_earned', 0)}")
                    with col3:
                        st.metric(label="New Total Progress", value=f"{result.get('new_total_progress', current_progress)}%")

                    st.info(f"**Feedback:** {result.get('feedback', '')}")
                    st.warning(f"**Next Step:** {result.get('next_step', '')}")

                except json.JSONDecodeError:
                    st.error("Failed to parse the response from the AI engine. Please try again.")
                    with st.expander("Raw Response"):
                        st.write(response.text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
