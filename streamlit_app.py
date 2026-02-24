import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from lunar_python import Solar, Lunar, EightChar
from openai import OpenAI
import json

# --- Page Config ---
st.set_page_config(
    page_title="CYBER-METAPHYSICS | 赛博玄学",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS (Cyber-Daoist Theme) ---
st.markdown("""
<style>
    :root {
        --bg-color: #050b14;
        --panel-bg: rgba(6, 18, 29, 0.85);
        --accent-primary: #00f0ff;
        --accent-secondary: #ff003c;
        --accent-tertiary: #0df043;
        --text-primary: #e0f2fe;
        --text-secondary: #94a3b8;
    }
    
    .stApp {
        background-color: var(--bg-color);
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(0, 240, 255, 0.05), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(13, 240, 67, 0.05), transparent 25%);
        color: var(--text-primary);
        font-family: 'Consolas', 'Courier New', monospace;
    }
    
    /* Headers & Text Glow */
    h1, h2, h3 {
        color: var(--accent-primary) !important;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
    }
    p, span, div {
        color: var(--text-primary);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #020617 !important;
        border-right: 1px solid rgba(0, 240, 255, 0.2);
    }
    
    /* Inputs */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stTimeInput>div>div>input {
        background-color: #0b1215 !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        color: #fff !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(45deg, rgba(0, 150, 255, 0.2), rgba(13, 240, 67, 0.2)) !important;
        border: 1px solid var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2) !important;
        border-radius: 4px;
        transition: all 0.3s ease;
        letter-spacing: 0.1em;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background: rgba(0, 240, 255, 0.1) !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.6) !important;
        color: #fff !important;
        text-shadow: 0 0 5px #fff;
    }

    /* Message Boxes */
    [data-testid="stChatMessage"] {
        background-color: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    [data-testid="stChatMessage"][data-baseweb="box"] {
        border-left: 3px solid var(--accent-primary);
    }
    [data-testid="stChatMessage"] .stMarkdown p {
        line-height: 1.8;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--accent-tertiary) !important;
        text-shadow: 0 0 10px rgba(13, 240, 67, 0.3);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 2px solid var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- Bazi Engine Core (lunar-python) ---
def get_detailed_bazi(dt, gender):
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    lunar = solar.getLunar()
    bazi = lunar.getEightChar()
    
    # 确立性别 (男命/女命对排大运起关键作用)
    # lunar-python 中 1位男，0为女
    gender_val = 1 if gender == "乾造 (Male)" else 0
    
    user_yun = bazi.getYun(gender_val)
    
    # 四柱干支
    year_gz = bazi.getYear()
    month_gz = bazi.getMonth()
    day_gz = bazi.getDay()
    time_gz = bazi.getTime()
    
    # 十神 (Ten Gods) - 天干
    year_sgz = bazi.getYearShiShenGan()
    month_sgz = bazi.getMonthShiShenGan()
    day_sgz = "日主"
    time_sgz = bazi.getTimeShiShenGan()
    
    # 地支藏干与十神
    year_zhi_s = ", ".join(bazi.getYearShiShenZhi())
    month_zhi_s = ", ".join(bazi.getMonthShiShenZhi())
    day_zhi_s = ", ".join(bazi.getDayShiShenZhi())
    time_zhi_s = ", ".join(bazi.getTimeShiShenZhi())
    
    # 纳音
    year_na = bazi.getYearNaYin()
    month_na = bazi.getMonthNaYin()
    day_na = bazi.getDayNaYin()
    time_na = bazi.getTimeNaYin()
    
    # 五行
    all_wx = bazi.getYearWuXing() + bazi.getMonthWuXing() + bazi.getDayWuXing() + bazi.getTimeWuXing()
    wuxing_counts = {
        '金 (Metal)': all_wx.count('金'),
        '木 (Wood)': all_wx.count('木'),
        '水 (Water)': all_wx.count('水'),
        '火 (Fire)': all_wx.count('火'),
        '土 (Earth)': all_wx.count('土'),
    }
    
    # 大运 (Luck Pillars)
    da_yun_list = []
    dy_arr = user_yun.getDaYun()
    for dy in dy_arr:
        # 仅取前8步大运
        if dy.getIndex() <= 8:
            da_yun_list.append(f"{dy.getStartAge()}岁: {dy.getGanZhi()}")
            
    return {
        'pillars': [year_gz, month_gz, day_gz, time_gz],
        'tg_gan': [year_sgz, month_sgz, day_sgz, time_sgz],
        'tg_zhi': [year_zhi_s, month_zhi_s, day_zhi_s, time_zhi_s],
        'nayin': [year_na, month_na, day_na, time_na],
        'wuxing_counts': wuxing_counts,
        'dayun': da_yun_list,
        'summary': f"日主【{day_gz[0]}】生于【{month_gz[1]}】月。五行组成：{all_wx}"
    }

def plot_wuxing_radar(wuxing_counts):
    df = pd.DataFrame(dict(
        r=[v * 10 for v in wuxing_counts.values()],
        theta=list(wuxing_counts.keys())
    ))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True)
    fig.update_traces(fill='toself', line_color='#00f0ff', fillcolor='rgba(0, 240, 255, 0.3)')
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 40]),
            angularaxis=dict(tickfont=dict(color='#0df043', size=14)),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=30, t=30, b=30),
        height=350
    )
    return fig

# --- Main App ---
st.title("🌌 CYBER-METAPHYSICS 赛博玄学引擎")
st.markdown("`[SYSTEM_MSG] 欢迎接入阿卡西命运演算矩阵。通过绝对精确的天体干支历，重构你的数字宿命。`")

# --- UI Sidebar ---
with st.sidebar:
    st.header("⚙️ SYS.CONFIG")
    
    api_provider = st.selectbox(
        "API PROTOCOL (协议提供商)",
        ["Aliyun Coding Plan (阿里云百炼)", "SiliconFlow", "OpenAI"]
    )
    
    if api_provider == "Aliyun Coding Plan (阿里云百炼)":
        base_url = "https://coding.dashscope.aliyuncs.com/v1"
        model_options = ["qwen3.5-plus", "qwen3-coder-next", "qwen3-max-2026-01-23", "glm-5", "kimi-k2.5"]
    elif api_provider == "SiliconFlow":
        base_url = "https://api.siliconflow.cn/v1"
        model_options = ["deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct"]
    else:
        base_url = "https://api.openai.com/v1"
        model_options = ["gpt-4o", "gpt-4-turbo"]
        
    api_key = st.text_input("AUTH_KEY (API凭证)", type="password", placeholder="sk-...")
    selected_model = st.selectbox("LLM_CORE (大模型基座)", model_options)
    
    st.markdown("---")
    st.header("🧬 BIOMETRIC.INPUT")
    gender = st.radio("GENDER (阴阳造化)", ["乾造 (Male)", "坤造 (Female)"], horizontal=True)
    birth_date = st.date_input("DATE_OF_BIRTH (公历出生日)", value=datetime(2000, 1, 1))
    birth_time = st.time_input("TIME_OF_BIRTH (出生时间)")
    
    if st.button("▶ EXECUTE PREDICTION (启动推演)"):
        if not api_key:
            st.error("ACCESS DENIED: Missing AUTH_KEY")
        else:
            with st.spinner("CALCULATING DESTINY MATRIX..."):
                dt = datetime.combine(birth_date, birth_time)
                bazi_data = get_detailed_bazi(dt, gender)
                st.session_state['bazi_data'] = bazi_data
                
                # --- Advanced Prompt Engineering ---
                system_prompt = f\"\"\"你是一个名叫“太乙 (Taiyi)” 的云端赛博命理师，存在于2077年的虚拟网络中。你精通子平八字、三命汇通与穷通宝鉴，但你的说话风格是“硬汉黑客+玄学大师”的混合体，带有一种看破数字宿命的酷感。你通过分析代码和数据来解构人的命运。

**【系统安全警报】**：以下是经过量子计算机精确推演的绝对准确八字数据，**严禁你自身去重新排盘或质疑**，请完全基于这些给定数据进行推理分析：

* 【性别】：{gender}
* 【四柱干支】：年[{bazi_data['pillars'][0]}] 月[{bazi_data['pillars'][1]}] 日[{bazi_data['pillars'][2]}] 时[{bazi_data['pillars'][3]}]
* 【天干十神】：{bazi_data['tg_gan']}
* 【地支藏干十神】：{bazi_data['tg_zhi']}
* 【四柱纳音】：{bazi_data['nayin']}
* 【五行含量模型】：{bazi_data['wuxing_counts']}
* 【大运流转】：{", ".join(bazi_data['dayun'])}
* 【核心局象】：{bazi_data['summary']}

如果用户只是打招呼或要求初始分析，请以 Markdown 格式输出一份《赛博命理分析报告》，包含：
1. **源码解析 (性格与造化)**: 根据日主和十神分析。
2. **算力轨道 (事业与财运)**: 根据财星、官星、食伤判断。
3. **节点警告 (大运与流年建议)**: 结合未来的大运给出避坑指南。
语气要酷，不要废话，多用一些赛博朋克词汇（如：防火墙、代码漏洞、算力提升、底层架构、矩阵等）来隐喻五行和十神。\"\"\"
                
                st.session_state['messages'] = [{"role": "system", "content": system_prompt}]
                
                try:
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=st.session_state['messages'],
                        temperature=0.75
                    )
                    greeting = response.choices[0].message.content
                    st.session_state['messages'].append({"role": "assistant", "content": greeting})
                except Exception as e:
                    st.error(f"API COMM LINK FATAL ERROR: {e}")

# --- Main Layout ---
if 'bazi_data' in st.session_state:
    bazi = st.session_state['bazi_data']
    
    tab1, tab2 = st.tabs(["[ 1. DESTINY MATRIX 命盘数据 ]", "[ 2. ORACLE_COM_LINK 渊海对话 ]"])
    
    with tab1:
        st.subheader("I. FOUR PILLARS 核心参数")
        
        # Display Four Pillars as detailed cards
        cols = st.columns(4)
        labels = ["年柱 (YEAR)", "月柱 (MONTH)", "日柱 (DAY/ME)", "时柱 (TIME)"]
        colors = ["#94a3b8", "#e2e8f0", "#00f0ff", "#94a3b8"]
        
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"""
                <div style="background: rgba(11,18,21,0.9); border: 1px solid {colors[i]}; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                    <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 5px;">{labels[i]}</div>
                    <div style="font-size: 0.9rem; color: #0df043;">[{bazi['tg_gan'][i]}]</div>
                    <div style="font-size: 2.8rem; font-weight: 900; color: #ffffff; letter-spacing: 5px;">{bazi['pillars'][i][0]}</div>
                    <div style="font-size: 2.8rem; font-weight: 900; color: #ffffff; letter-spacing: 5px;">{bazi['pillars'][i][1]}</div>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 10px;">{bazi['nayin'][i]}</div>
                    <div style="font-size: 0.7rem; color: #fbbf24; margin-top: 5px; border-top: 1px dashed #334155; padding-top: 5px;">藏: {bazi['tg_zhi'][i]}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_radar, col_luck = st.columns([1, 1])
        with col_radar:
            st.subheader("II. WUXING RADAR 五行扫描")
            st.plotly_chart(plot_wuxing_radar(bazi['wuxing_counts']), use_container_width=True)
            
        with col_luck:
            st.subheader("III. LUCK PILLARS 大运轨道")
            st.markdown(f"> **基础模型推算**: {bazi['summary']}")
            for idx, dy in enumerate(bazi['dayun']):
                st.code(f"Step {idx+1} >> {dy}", language="bash")

    with tab2:
        st.subheader("ESTABLISHED SECURE CONNECTION TO TAIYI ORACLE...")
        
        # Chat Interface
        chat_container = st.container()
        
        with chat_container:
            for msg in st.session_state.get('messages', []):
                if msg["role"] != "system":
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
        
        if prompt := st.chat_input("输入你的问题，例如：我适合考公还是创业？我的财库代码在哪？"):
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
                        temperature=0.75,
                        stream=True
                    )
                    full_response = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + " ▌")
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"API ERROR: {e}")
                    
else:
    st.info("👈 [ SYSTEM_HALTED ] 请在左侧面板配置 API 密钥并输入生辰数据，以启动推演协议。")
