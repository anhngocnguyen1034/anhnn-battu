import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from lunar_python import Solar, Lunar, EightChar
from openai import OpenAI
import json

# --- Page Configuration (Minimalist Neo-Daoist) ---
st.set_page_config(
    page_title="玄冥 | MING MATRIX",
    page_icon="☯️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Aesthetic Injection (Neo-Daoist Clean Dark Theme) ---
st.markdown("""
<style>
    :root {
        --bg-color: #0d1117;
        --panel-bg: rgba(22, 27, 34, 0.6);
        --accent-gold: #d4af37;
        --accent-silver: #c0c0c0;
        --accent-jade: #50c878;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --border-color: #30363d;
    }
    
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
    }
    
    /* Typography */
    h1, h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 300;
        letter-spacing: 0.1em;
        margin-bottom: 0.5em;
    }
    .chinese-serif {
        font-family: "Noto Serif SC", "Songti SC", serif;
        font-weight: 500;
    }
    h1 .chinese-serif, h2 .chinese-serif, h3 .chinese-serif {
        color: var(--accent-gold);
    }
    
    /* Controls & Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid var(--border-color);
    }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input, .stTimeInput>div>div>input {
        background-color: #0d1117 !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 6px;
    }
    
    /* Elegant Buttons */
    .stButton>button {
        background-color: transparent !important;
        border: 1px solid var(--accent-gold) !important;
        color: var(--accent-gold) !important;
        border-radius: 4px;
        transition: all 0.3s ease;
        letter-spacing: 0.15em;
        font-family: "Noto Serif SC", serif;
    }
    .stButton>button:hover {
        background-color: rgba(212, 175, 55, 0.1) !important;
        color: #fff !important;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);
    }

    /* Message Boxes & Container Cards */
    [data-testid="stChatMessage"] {
        background-color: transparent;
        border: none;
        padding: 0;
        margin-bottom: 24px;
    }
    [data-testid="stChatMessage"][data-baseweb="box"] .stMarkdown {
        background-color: var(--panel-bg);
        border-radius: 8px;
        padding: 16px 20px;
        border: 1px solid var(--border-color);
    }
    
    /* Bazi Grid Display */
    .bazi-pillar {
        background: var(--panel-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px 10px;
        text-align: center;
        transition: transform 0.2s ease;
    }
    .bazi-pillar:hover {
        border-color: var(--accent-gold);
        transform: translateY(-2px);
    }
    .pillar-header { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 8px; }
    .god-gan { font-size: 0.85rem; color: var(--accent-silver); margin-bottom: 4px; }
    .gan { font-size: 2.2rem; font-weight: bold; color: var(--text-primary); line-height: 1.1; }
    .zhi { font-size: 2.2rem; font-weight: bold; color: var(--text-primary); line-height: 1.1; margin-bottom: 8px; }
    .nayin { font-size: 0.75rem; color: var(--accent-gold); margin-bottom: 8px; }
    .god-zhi { font-size: 0.75rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 8px; }
    .shensha { font-size: 0.75rem; color: var(--accent-jade); margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# --- Calculation Core (lunar-python) ---
def get_shensha_list(shensha_dict):
    """提取吉神凶煞并格式化"""
    if not shensha_dict: return ""
    return " ".join([k for k in shensha_dict.keys()])

def calculate_professional_bazi(dt, gender_str):
    """
    严谨计算八字各项基础参数：原局、大运、十神、纳音、神煞等
    """
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    lunar = solar.getLunar()
    bazi = lunar.getEightChar()
    
    gender_val = 1 if gender_str == "乾造 (Male)" else 0
    
    # 基础四柱干支
    ygz, mgz, dgz, tgz = bazi.getYear(), bazi.getMonth(), bazi.getDay(), bazi.getTime()
    
    # 十神
    tg_gan = [bazi.getYearShiShenGan(), bazi.getMonthShiShenGan(), "日主", bazi.getTimeShiShenGan()]
    tg_zhi = [
        " ".join(bazi.getYearShiShenZhi()),
        " ".join(bazi.getMonthShiShenZhi()),
        " ".join(bazi.getDayShiShenZhi()),
        " ".join(bazi.getTimeShiShenZhi())
    ]
    
    # 纳音
    nayin = [bazi.getYearNaYin(), bazi.getMonthNaYin(), bazi.getDayNaYin(), bazi.getTimeNaYin()]
    
    # 吉神凶煞 (Shen Sha)
    ss = [
        get_shensha_list(bazi.getYearShenSha()), 
        get_shensha_list(bazi.getMonthShenSha()), 
        get_shensha_list(bazi.getDayShenSha()), 
        get_shensha_list(bazi.getTimeShenSha())
    ]
    
    # 五行能量统计
    all_wx = bazi.getYearWuXing() + bazi.getMonthWuXing() + bazi.getDayWuXing() + bazi.getTimeWuXing()
    wuxing = {
        '金(Metal)': all_wx.count('金'),
        '木(Wood)': all_wx.count('木'),
        '水(Water)': all_wx.count('水'),
        '火(Fire)': all_wx.count('火'),
        '土(Earth)': all_wx.count('土'),
    }
    
    # 大运推演
    user_yun = bazi.getYun(gender_val)
    da_yun = []
    try:
        dy_arr = user_yun.getDaYun()
        for dy in dy_arr:
            if 0 < dy.getIndex() <= 10:  # 提取前10步大运
                da_yun.append({
                    "start_age": dy.getStartAge(),
                    "start_year": dy.getStartYear(),
                    "ganzhi": dy.getGanZhi()
                })
    except Exception as e:
        da_yun = [{"start_age": 0, "start_year": dt.year, "ganzhi": "计算受限"}]
        
    # 其他专业参数：命宫、胎元
    ming_gong = bazi.getMingGong()
    tai_yuan = bazi.getTaiYuan()
    
    return {
        "gender": gender_str,
        "pillars": [ygz, mgz, dgz, tgz],
        "tg_gan": tg_gan,
        "tg_zhi": tg_zhi,
        "nayin": nayin,
        "shensha": ss,
        "wuxing": wuxing,
        "dayun": da_yun,
        "minggong": ming_gong,
        "taiyuan": tai_yuan,
        "wuxing_str": all_wx,
        "day_master": dgz[0]
    }

def get_annual_fortune(year: int):
    """
    Tool: 用于计算指定年份的干支和流年五行属性
    因为大模型容易算错流年干支，此工具可通过 lunar-python 绝对准确地获取该年干支。
    """
    solar = Solar.fromYmdHms(year, 1, 1, 12, 0, 0)
    lunar = solar.getLunar()
    gz = lunar.getYearInGanZhi()
    wx = lunar.getYearNaYin()
    return json.dumps({
        "year": year,
        "ganzhi": gz,
        "nayin": wx,
        "context": f"当年干支为{gz}，纳音{wx}。你可以结合命主原局进行生克制化分析。"
    })

# --- UI Render Helpers ---
def render_wuxing_chart(wuxing):
    df = pd.DataFrame(dict(
        r=[v * 20 for v in wuxing.values()],
        theta=list(wuxing.keys())
    ))
    fig = px.line_polar(df, r='r', theta='theta', line_close=True)
    fig.update_traces(fill='toself', line_color='#d4af37', fillcolor='rgba(212, 175, 55, 0.2)')
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 80]),
            angularaxis=dict(tickfont=dict(color='#8b949e', size=13)),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=250
    )
    return fig

# --- Agentic AI Configuration & Prompts ---

# 专为百炼优化的 Tools Schema
bazi_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_annual_fortune",
            "description": "当用户问及具体某一年的运势（例如：2026年我会怎么样？我哪一年容易发财？），调用此工具获取该公历年的准确干支和纳音属性组合，从而进行流年命理分析。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "公历年份，格式如 2026"
                    }
                },
                "required": ["year"]
            }
        }
    }
]

def build_system_prompt(bazi_data):
    dy_str = " | ".join([f"{d['start_year']}年({d['start_age']}岁)起: {d['ganzhi']}" for d in bazi_data['dayun']])
    
    return f"""你是一位正统且极具专业素养的新中式命理大师，名为「玄冥」。你精通子平八字、穷通宝鉴与滴天髓，擅长用现代化、克制、优美的文字去解构人的命运。不准使用廉价的机器语言或迷信恐吓的话术，要像一位知性的哲学家。

**【命理先天参数 - 绝对真理，禁止篡改】**
- **性别**：{bazi_data['gender']}
- **命宫**：{bazi_data['minggong']} | **胎元**：{bazi_data['taiyuan']}
- **日主 (Day Master)**：{bazi_data['day_master']}

**【四柱原局分布】**：
- 年柱 (祖业/早年)：{bazi_data['pillars'][0]} | 藏：{bazi_data['tg_zhi'][0]} | 纳音：{bazi_data['nayin'][0]}
- 月柱 (父母/青年)：{bazi_data['pillars'][1]} | 藏：{bazi_data['tg_zhi'][1]} | 纳音：{bazi_data['nayin'][1]}
- 日柱 (夫妻/中年)：{bazi_data['pillars'][2]} | 藏：{bazi_data['tg_zhi'][2]} | 纳音：{bazi_data['nayin'][2]}
- 时柱 (子女/晚年)：{bazi_data['pillars'][3]} | 藏：{bazi_data['tg_zhi'][3]} | 纳音：{bazi_data['nayin'][3]}

**【后天大运轨迹】**：
{dy_str}

**交互要求**：
1. 你的回答必须使用 Markdown 格式排版，确保优美易读。
2. 结合日主的生克制化与五行十神强弱进行深度批改。
3. 如果用户询问未来某年的运势，你应该**优先调用 `get_annual_fortune` 工具**以确保推得的流年干支绝对正确（防止大模型在干支纪年上产生数学幻觉），并在工具返回流年干支后，结合原局与当前所处的大运，给出三才交互（原局-大运-流年）的影响分析！
"""

# --- Application Entry ---
st.title("玄冥 | <span class='chinese-serif'>命理架构终端</span>", unsafe_allow_html=True)
st.markdown("秉持传统数术严谨，重构当代命运图谱。")

# [ Sidebar Settings ]
with st.sidebar:
    st.header("🔑 ALIYUN CODING PLAN")
    # 按照您的要求，内置百炼 Coding Plan 端点和核心参数
    st.info("百炼专区: 顶级推理模型支持 Function Calling")
    api_key = st.text_input("AUTH KEY", type="password", value="sk-sp-0b28da8e3f404df182c05d3fd45787a5")
    selected_model = st.selectbox("LLM MODEL", ["qwen3.5-plus", "qwen3-coder-plus", "glm-4.7"])
    base_url = "https://coding.dashscope.aliyuncs.com/v1"
    
    st.markdown("---")
    st.header("📜 四柱排盘 (BAZI INPUT)")
    gender = st.radio("系统性别", ["乾造 (Male)", "坤造 (Female)"])
    birth_date = st.date_input("公历出生日", value=datetime(1990, 6, 15))
    birth_time = st.time_input("出生时间 (时辰)")
    
    if st.button("生成命盘体系 (GENERATE)"):
        with st.spinner("推算先天数据矩阵..."):
            dt = datetime.combine(birth_date, birth_time)
            bazi = calculate_professional_bazi(dt, gender)
            st.session_state['bazi_data'] = bazi
            
            # Reset Chat Engine
            st.session_state['messages'] = [
                {"role": "system", "content": build_system_prompt(bazi)}
            ]
            st.session_state['chat_history'] = []
            
            # Initial Greeting Auto-Generation
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                resp = client.chat.completions.create(
                    model=selected_model,
                    messages=st.session_state['messages'],
                    temperature=0.6,
                )
                greeting = resp.choices[0].message.content
                st.session_state['messages'].append({"role": "assistant", "content": greeting})
                st.session_state['chat_history'].append({"role": "assistant", "content": greeting})
            except Exception as e:
                st.error(f"连接阿里云百炼失败: {e}")

# [ Main Dashboard ]
if 'bazi_data' in st.session_state:
    bzi = st.session_state['bazi_data']
    
    col_matrix, col_chat = st.columns([1, 1.2])
    
    with col_matrix:
        st.subheader("<span class='chinese-serif'>八字原局</span> (NATIVE MATRIX)", unsafe_allow_html=True)
        
        # Pillars Rendering
        cols = st.columns(4)
        labels = ["年柱 (祖业)", "月柱 (机缘)", "日柱 (本我)", "时柱 (晚成)"]
        
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"""
                <div class="bazi-pillar">
                    <div class="pillar-header">{labels[i]}</div>
                    <div class="god-gan">{bzi['tg_gan'][i]}</div>
                    <div class="gan">{bzi['pillars'][i][0]}</div>
                    <div class="zhi">{bzi['pillars'][i][1]}</div>
                    <div class="nayin">{bzi['nayin'][i]}</div>
                    <div class="god-zhi">藏干: {bzi['tg_zhi'][i]}</div>
                    <div class="shensha">{bzi['shensha'][i]}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # Energy & Luck Pillars
        cols_bottom = st.columns([1, 1.2])
        with cols_bottom[0]:
            st.markdown(f"**命宫**: {bzi['minggong']} &nbsp;|&nbsp; **胎元**: {bzi['taiyuan']}")
            st.plotly_chart(render_wuxing_chart(bzi['wuxing']), use_container_width=True)
            
        with cols_bottom[1]:
            st.markdown("**后天大运轨迹** (Luck Pillars)")
            for d in bzi['dayun']:
                st.markdown(f"`{d['start_year']} (起于{d['start_age']}岁) -> {d['ganzhi']}`")

    with col_chat:
        st.subheader("<span class='chinese-serif'>命理论道</span> (ORACLE ENGINE)", unsafe_allow_html=True)
        
        # Chat Rendering
        for msg in st.session_state['chat_history']:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        # Interactive Tool-Calling Chat Loop
        if prompt := st.chat_input("向玄冥大师提问 (如：我何时能遇正缘？2026年我的运势如何？)"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                try:
                    # 第一轮请求 (带 Tools)
                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=st.session_state.messages,
                        tools=bazi_tools,
                        tool_choice="auto"
                    )
                    
                    response_message = response.choices[0].message
                    
                    # 检查大模型是否决定调用工具 (e.g., 查流年)
                    if response_message.tool_calls:
                        st.session_state.messages.append(response_message)
                        
                        for tool_call in response_message.tool_calls:
                            if tool_call.function.name == "get_annual_fortune":
                                try:
                                    args = json.loads(tool_call.function.arguments)
                                    year_requested = args.get("year", datetime.now().year)
                                except:
                                    year_requested = datetime.now().year
                                    
                                st.toast(f"🔮 引擎推演流年干支: 面向 {year_requested} 年...", icon="⚖️")
                                tool_result = get_annual_fortune(year_requested)
                                
                                st.session_state.messages.append({
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": tool_call.function.name,
                                    "content": tool_result
                                })
                                
                        # 发起第二次带结果的聊天流式请求
                        second_response = client.chat.completions.create(
                            model=selected_model,
                            messages=st.session_state.messages,
                            stream=True
                        )
                        
                        full_res = ""
                        for chunk in second_response:
                            if chunk.choices[0].delta.content:
                                full_res += chunk.choices[0].delta.content
                                message_placeholder.markdown(full_res + " ▌")
                        message_placeholder.markdown(full_res)
                        
                        st.session_state.messages.append({"role": "assistant", "content": full_res})
                        st.session_state.chat_history.append({"role": "assistant", "content": full_res})
                        
                    else:
                        full_res = response_message.content or "天机不可泄露。"
                        message_placeholder.markdown(full_res)
                        st.session_state.messages.append({"role": "assistant", "content": full_res})
                        st.session_state.chat_history.append({"role": "assistant", "content": full_res})
                        
                except Exception as e:
                    st.error(f"引擎同步异常: {e}")

else:
    st.info("👈 调校左侧八字参数，进入命运罗盘。")
