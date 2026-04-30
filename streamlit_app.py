import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from openai import OpenAI

from engine import calculate_professional_bazi
from prompts import build_system_prompt
from tools import TOOL_SCHEMAS, dispatch_tool
from agent import get_messages_for_api, run_react_loop

st.set_page_config(
    page_title="玄冥 | MING MATRIX",
    page_icon="☯️",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    h1 .chinese-serif, h2 .chinese-serif, h3 .chinese-serif { color: var(--accent-gold); }
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
    label, .stRadio label p { color: var(--text-primary) !important; }
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 2rem !important; }
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
    [data-testid="stChatMessage"] { background-color: transparent; border: none; padding: 0; margin-bottom: 24px; }
    [data-testid="stChatMessage"][data-baseweb="box"] .stMarkdown {
        background-color: var(--panel-bg);
        border-radius: 8px;
        padding: 16px 20px;
        border: 1px solid var(--border-color);
    }
    .stMarkdown p, .stMarkdown li, [data-testid="stChatMessage"] p {
        color: var(--text-primary) !important;
        line-height: 1.6;
        font-size: 1.05rem;
    }
    .bazi-pillar {
        background: var(--panel-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px 10px;
        text-align: center;
        transition: transform 0.2s ease;
    }
    .bazi-pillar:hover { border-color: var(--accent-gold); transform: translateY(-2px); }
    .pillar-header { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 8px; }
    .god-gan { font-size: 0.85rem; color: var(--accent-silver); margin-bottom: 4px; }
    .gan, .zhi { font-size: 2.2rem; font-weight: bold; color: var(--text-primary); line-height: 1.1; margin-bottom: 8px; }
    .nayin { font-size: 0.75rem; color: var(--accent-gold); margin-bottom: 8px; }
    .god-zhi { font-size: 0.75rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 8px; }
    .shensha { font-size: 0.75rem; color: var(--accent-jade); margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


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


PROVIDER_PRESETS = {
    "阿里云百炼": {
        "base_url": "https://coding.dashscope.aliyuncs.com/v1",
        "models": ["qwen3.5-plus", "qwen3-coder-plus", "qwen-plus", "qwen-max"],
        "env_key": "DASHSCOPE_API_KEY",
    },
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "env_key": "OPENAI_API_KEY",
    },
    "Anthropic (兼容)": {
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        "env_key": "ANTHROPIC_API_KEY",
    },
    "MiMo": {
        "base_url": "https://token-plan-cn.xiaomimimo.com/anthropic",
        "models": ["mimo-v2.5-pro"],
        "env_key": "ANTHROPIC_AUTH_TOKEN",
    },
    "自定义 (Custom)": {
        "base_url": "",
        "models": [],
        "env_key": "",
    },
}


def _get_default_api_key(env_key: str) -> str:
    if env_key and hasattr(st, "secrets") and st.secrets.get(env_key):
        return st.secrets[env_key]
    if env_key:
        return os.environ.get(env_key, "")
    return ""


st.markdown("<h1>玄冥 | <span class='chinese-serif'>命理架构终端</span></h1>", unsafe_allow_html=True)
st.markdown("秉持传统数术严谨，重构当代命运图谱。")

with st.sidebar:
    st.header("⚙️ 模型配置 (MODEL CONFIG)")

    provider = st.selectbox("服务商 (Provider)", list(PROVIDER_PRESETS.keys()), index=0)
    preset = PROVIDER_PRESETS[provider]

    if provider == "自定义 (Custom)":
        base_url = st.text_input("API Base URL", placeholder="https://your-api.com/v1")
        custom_model = st.text_input("模型名称 (Model)", placeholder="gpt-4o")
        selected_model = custom_model
        env_key = st.text_input("环境变量名 (可选)", placeholder="MY_API_KEY")
    else:
        base_url = preset["base_url"]
        selected_model = st.selectbox("模型 (Model)", preset["models"])
        env_key = preset["env_key"]

    default_key = _get_default_api_key(env_key)
    api_key = st.text_input(
        "API Key",
        type="password",
        value=default_key or "",
        placeholder=f"输入 Key 或设置环境变量 {env_key}",
    )
    api_key = api_key.strip() or default_key

    if provider != "自定义 (Custom)":
        with st.expander("高级设置"):
            base_url = st.text_input("Base URL (可修改)", value=base_url)
            custom_model_override = st.text_input("模型名 (留空用上方选择)", placeholder="留空则使用下拉选择")
            if custom_model_override.strip():
                selected_model = custom_model_override.strip()

    st.markdown("---")
    st.header("📜 四柱排盘 (BAZI INPUT)")
    gender = st.radio("系统性别", ["乾造 (Male)", "坤造 (Female)"])
    birth_date = st.date_input(
        "公历出生日",
        value=datetime(1990, 6, 15),
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2100, 1, 1)
    )
    birth_time = st.time_input("出生时间 (时辰)")

    if st.button("生成命盘体系 (GENERATE)"):
        with st.spinner("推算先天数据矩阵..."):
            dt = datetime.combine(birth_date, birth_time)
            bazi = calculate_professional_bazi(dt, gender)
            st.session_state['bazi_data'] = bazi
            st.session_state['messages'] = [
                {"role": "system", "content": build_system_prompt(bazi)}
            ]
            st.session_state['chat_history'] = []

            if api_key:
                try:
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    resp = client.chat.completions.create(
                        model=selected_model,
                        messages=st.session_state['messages'],
                        temperature=0.6,
                    )
                    greeting = (resp.choices[0].message.content or "").strip()
                    if greeting:
                        st.session_state['messages'].append({"role": "assistant", "content": greeting})
                        st.session_state['chat_history'].append({"role": "assistant", "content": greeting})
                except Exception as e:
                    st.error(f"API 调用失败: {e}")
            else:
                st.warning(f"未配置 API Key，请在侧边栏填写或设置环境变量 {env_key}。")

if 'bazi_data' in st.session_state:
    bzi = st.session_state['bazi_data']
    col_matrix, col_chat = st.columns([1, 1.2])

    with col_matrix:
        st.markdown("<h3><span class='chinese-serif'>八字原局</span> (NATIVE MATRIX)</h3>", unsafe_allow_html=True)
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
        cols_bottom = st.columns([1, 1.2])
        with cols_bottom[0]:
            st.markdown(f"**命宫**: {bzi['minggong']} &nbsp;|&nbsp; **胎元**: {bzi['taiyuan']}")
            st.plotly_chart(render_wuxing_chart(bzi['wuxing']), use_container_width=True)
        with cols_bottom[1]:
            st.markdown("**后天大运轨迹** (Luck Pillars)")
            for d in bzi['dayun']:
                st.markdown(f"`{d['start_year']} (起于{d['start_age']}岁) -> {d['ganzhi']}`")

    with col_chat:
        st.markdown("<h3><span class='chinese-serif'>命理论道</span> (ORACLE ENGINE)</h3>", unsafe_allow_html=True)
        for msg in st.session_state.get('chat_history', []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("向玄冥大师提问 (如：我何时能遇正缘？2026年我的运势如何？)"):
            st.session_state.setdefault('chat_history', []).append({"role": "user", "content": prompt})
            st.session_state.setdefault('messages', []).append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                if not api_key:
                    message_placeholder.markdown("请先在侧边栏配置 API Key。")
                else:
                    try:
                        client = OpenAI(api_key=api_key, base_url=base_url)
                        messages_for_api = get_messages_for_api(st.session_state['messages'])
                        final_content, updated_messages, fact_check_results = run_react_loop(
                            client,
                            selected_model,
                            messages_for_api,
                            TOOL_SCHEMAS,
                            dispatch_tool,
                            bazi_data=st.session_state['bazi_data'],
                            max_steps=8,
                            do_fact_check=True,
                        )
                        st.session_state['messages'] = updated_messages
                        message_placeholder.markdown(final_content)
                        st.session_state['chat_history'].append({"role": "assistant", "content": final_content})
                        if fact_check_results:
                            for fc in fact_check_results:
                                st.warning(f"Fact-Check: {fc.get('year')}年 声称「{fc.get('claimed')}」实际为「{fc.get('actual')}」，已按实际校正。")
                    except Exception as e:
                        st.error(f"引擎同步异常: {e}")

else:
    st.info("👈 调校左侧八字参数，进入命运罗盘。")
