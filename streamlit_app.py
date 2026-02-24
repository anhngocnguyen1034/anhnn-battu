import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from lunar_python import Solar, Lunar, EightChar
from openai import OpenAI
import json

# --- Page Config ---
st.set_page_config(
    page_title="CYBER-BAZI | 赛博玄学",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS (Cyber-Daoist Theme) ---
st.markdown("""
<style>
    /* Dark Theme & Cyberpunk Colors */
    :root {
        --bg-color: #020617;
        --panel-bg: rgba(15, 23, 42, 0.7);
        --accent-primary: #10b981;
        --accent-secondary: #06b6d4;
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
    }
    
    .stApp {
        background-color: var(--bg-color);
        background-image: radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.05) 0%, transparent 60%);
        color: var(--text-primary);
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--accent-primary) !important;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    /* Input fields */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stTimeInput>div>div>input {
        background-color: #0b1215 !important;
        border: 1px solid rgba(16, 185, 129, 0.5) !important;
        color: var(--accent-secondary) !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, rgba(6, 95, 70, 0.8), rgba(22, 78, 99, 0.8)) !important;
        border: 1px solid var(--accent-primary) !important;
        color: #fff !important;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.2) !important;
        transition: all 0.3s ease;
        letter-spacing: 0.2em;
        font-weight: bold;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(6, 182, 212, 0.4) !important;
        border-color: var(--accent-secondary) !important;
    }

    /* Cards/Containers */
    .css-1r6slb0, [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: var(--panel-bg);
        border: 1px solid rgba(6, 182, 212, 0.2);
        border-radius: 10px;
        padding: 20px;
        backdrop-filter: blur(10px);
    }
    
    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background-color: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 8px;
        margin-bottom: 15px;
    }
    [data-testid="stChatMessage"][data-baseweb="box"] {
        border-left: 3px solid var(--accent-primary);
    }
</style>
""", unsafe_allow_html=True)

# --- Bazi Engine (lunar-python) ---
def calculate_bazi(dt):
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    lunar = solar.getLunar()
    bazi = lunar.getEightChar()
    
    year_gz = bazi.getYear()
    month_gz = bazi.getMonth()
    day_gz = bazi.getDay()
    time_gz = bazi.getTime()
    
    # 简易五行统计 (包含地支藏干的主气)
    year_wx = bazi.getYearWuXing()
    month_wx = bazi.getMonthWuXing()
    day_wx = bazi.getDayWuXing()
    time_wx = bazi.getTimeWuXing()
    
    all_wx = year_wx + month_wx + day_wx + time_wx
    
    wuxing_counts = {
        'Metal (金)': all_wx.count('金'),
        'Wood (木)': all_wx.count('木'),
        'Water (水)': all_wx.count('水'),
        'Fire (火)': all_wx.count('火'),
        'Earth (土)': all_wx.count('土'),
    }
    
    return {
        'bazi_str': f"{year_gz} {month_gz} {day_gz} {time_gz}",
        'wuxing_str': f"年:{year_wx} 月:{month_wx} 日:{day_wx} 时:{time_wx}",
        'wuxing_counts': wuxing_counts,
        'year_gz': year_gz,
        'month_gz': month_gz,
        'day_gz': day_gz,
        'time_gz': time_gz
    }

def plot_wuxing_radar(wuxing_counts):
    df = pd.DataFrame(dict(
        r=[v * 20 for v in wuxing_counts.values()],
        theta=list(wuxing_counts.keys())
    ))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True)
    fig.update_traces(fill='toself', line_color='#10b981')
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 100]),
            angularaxis=dict(tickfont=dict(color='#06b6d4', size=12))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=300
    )
    return fig

# --- Main App ---
st.title("CYBER-METAPHYSICS 赛博玄学")
st.markdown("`[SYSTEM INITIATED] AWAITING BIOMETRIC TEMPORAL DATA...`")

# Sidebar - Settings & Input
with st.sidebar:
    st.header("⚙️ SYSTEM.CONFIG")
    
    api_provider = st.selectbox(
        "API Provider",
        ["Aliyun Coding Plan (阿里云百炼)", "SiliconFlow", "OpenAI"]
    )
    
    # Provider specifics
    if api_provider == "Aliyun Coding Plan (阿里云百炼)":
        base_url = "https://coding.dashscope.aliyuncs.com/v1"
        model_options = ["qwen3.5-plus", "qwen3-max-2026-01-23", "qwen3-coder-next", "glm-5", "kimi-k2.5"]
    elif api_provider == "SiliconFlow":
        base_url = "https://api.siliconflow.cn/v1"
        model_options = ["deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct"]
    else:
        base_url = "https://api.openai.com/v1"
        model_options = ["gpt-4o", "gpt-4-turbo"]
        
    api_key = st.text_input("API KEY", type="password", placeholder="sk-...")
    selected_model = st.selectbox("LLM Core", model_options)
    
    st.markdown("---")
    st.header("🧬 TEMPORAL.INPUT")
    birth_date = st.date_input("BIRTH DATE (SOLAR)")
    birth_time = st.time_input("BIRTH TIME")
    
    if st.button("EXECUTE PREDICTION"):
        if not api_key:
            st.error("Missing API KEY")
        else:
            # Calculate Bazi
            dt = datetime.combine(birth_date, birth_time)
            bazi_data = calculate_bazi(dt)
            st.session_state['bazi_data'] = bazi_data
            
            # Reset chat
            system_prompt = f\"\"\"你是一位极具赛博朋克风格的“云端命理师”。你精通子平八字和五行，说话像个高级AI计算终端，带点赛博黑客的幽默感。
用户当前的命运基础数据（绝对准确，禁止重新推算）：
四柱代码：{bazi_data['bazi_str']}
五行能量：{bazi_data['wuxing_str']}

请基于上述底层数据，用一段话为用户做核心批语（Markdown格式）。\"\"\"
            
            st.session_state['messages'] = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Generate initial greeting
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=st.session_state['messages'],
                    temperature=0.7
                )
                greeting = response.choices[0].message.content
                st.session_state['messages'].append({"role": "assistant", "content": greeting})
            except Exception as e:
                st.error(f"API Error: {e}")

# Main Layout
if 'bazi_data' in st.session_state:
    bazi = st.session_state['bazi_data']
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("DECODED MATRIX")
        # Custom display for Bazi characters
        bazi_cols = st.columns(4)
        labels = ["YEAR (年)", "MONTH (月)", "DAY (日)", "TIME (时)"]
        pillars = [bazi['year_gz'], bazi['month_gz'], bazi['day_gz'], bazi['time_gz']]
        
        for i, col in enumerate(bazi_cols):
            with col:
                st.markdown(f"""
                <div style="text-align:center; padding: 10px; background: rgba(11, 18, 21, 0.8); border: 1px solid #065f46; border-radius: 5px;">
                    <div style="font-size: 0.7rem; color: #06b6d4;">{labels[i]}</div>
                    <div style="font-size: 1.8rem; font-weight: bold; color: #10b981;">{pillars[i][0]}</div>
                    <div style="font-size: 1.8rem; font-weight: bold; color: #34d399;">{pillars[i][1]}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br/>", unsafe_allow_html=True)
        st.subheader("WUXING RADAR")
        st.plotly_chart(plot_wuxing_radar(bazi['wuxing_counts']), use_container_width=True)

    with col2:
        st.subheader("ORACLE COM.LINK")
        
        # Display chat messages
        for msg in st.session_state.get('messages', []):
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # Chat input
        if prompt := st.chat_input("Input your query to the Oracle..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                try:
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=st.session_state.messages,
                        temperature=0.7,
                        stream=True
                    )
                    full_response = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"API Error: {e}")
else:
    st.info("👈 Enter your details in the SYS.CONFIG panel and EXECUTE PREDICTION.")
