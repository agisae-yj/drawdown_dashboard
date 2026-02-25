"""
Drawdown Monitor - 고점 대비 낙폭 대시보드
설치: pip install streamlit yfinance plotly pandas
실행: python3 -m streamlit run ~/Desktop/drawdown_dashboard.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Drawdown Monitor", page_icon="📉", layout="wide")

CATEGORIES = {
    "🚀 양자/우주/에너지": {
        "color": "#a78bfa",
        "tickers": {
            "IONQ": "아이언큐", "TEM": "Tempus AI", "RKLB": "로켓 랩",
            "LUNR": "인튜이티브 머신스", "OKLO": "오클로", "SMR": "뉴스케일 파워",
            "UUUU": "에너지 퓨얼스", "LEU": "센트러스 에너지",
            "FLNC": "플루언스 에너지", "BE": "블룸 에너지",
        }
    },
    "🛡️ 보안/방산/인프라": {
        "color": "#34d399",
        "tickers": {
            "PANW": "팔로알토 네트웍스", "CRWD": "크라우드스트라이크",
            "LHX": "L3해리스 테크놀로지스", "FTI": "테크닙FMC",
            "GEV": "GE 버노바", "VRT": "버티브 홀딩스",
            "XYL": "자일럼", "DE": "존 디어", "J": "제이콥스 솔루션스",
        }
    },
    "💻 빅테크/AI": {
        "color": "#60a5fa",
        "tickers": {
            "NVDA": "엔비디아", "MSFT": "마이크로소프트", "META": "메타 플랫폼스",
            "GOOGL": "알파벳 A", "GOOG": "알파벳 C", "AMZN": "아마존",
            "AAPL": "애플", "TSLA": "테슬라", "PLTR": "팔란티어",
            "ORCL": "오라클", "NFLX": "넷플릭스", "ASTS": "AST 스페이스모바일",
        }
    },
    "🏦 금융/자산운용": {
        "color": "#fbbf24",
        "tickers": {
            "JPM": "JP모건 체이스", "GS": "골드만삭스",
            "AXP": "아메리칸 익스프레스", "V": "비자",
            "MA": "마스터카드", "BLK": "블랙록", "BX": "블랙스톤",
        }
    },
    "🧪 헬스케어/기타": {
        "color": "#f472b6",
        "tickers": {
            "JNJ": "존슨앤존슨", "NEE": "넥스트에라 에너지", "LIN": "린데",
            "COST": "코스트코", "LVMUY": "LVMH ADR",
            "NTLA": "인텔리아 테라퓨틱스", "CRSP": "크리스퍼 테라퓨틱스",
            "BRK-B": "버크셔 해서웨이 B",
        }
    },
    "📈 ETF & 자산": {
        "color": "#fb923c",
        "tickers": {
            "VOO": "S&P 500 ETF", "QQQ": "나스닥 100 ETF",
            "XLV": "헬스케어 섹터 ETF", "TLT": "20년 국채 ETF",
            "SCHD": "배당성장주 ETF", "GLD": "금 ETF", "SLV": "은 ETF",
            "CPER": "구리 ETF", "LIT": "리튬 ETF", "QS": "퀀텀스케이프",
            "COIN": "코인베이스", "ETH-USD": "이더리움", "DJT": "트럼프 미디어",
        }
    },
}

ALL_TICKERS = {}
TICKER_TO_CAT = {}
for cat_name, cat_data in CATEGORIES.items():
    for t, n in cat_data["tickers"].items():
        ALL_TICKERS[t] = n
        TICKER_TO_CAT[t] = cat_name

def get_dd_color(dd):
    if dd > -5:   return "#16a34a"
    if dd > -10:  return "#15803d"
    if dd > -20:  return "#b45309"
    if dd > -35:  return "#c2410c"
    return "#b91c1c"

def get_dd_bg(dd):
    if dd > -5:   return "#f0fdf4"
    if dd > -10:  return "#dcfce7"
    if dd > -20:  return "#fffbeb"
    if dd > -35:  return "#fff7ed"
    return "#fef2f2"

def get_dd_label(dd):
    if dd > -5:   return "🟢 양호"
    if dd > -10:  return "🟢 안정"
    if dd > -20:  return "🟡 주의"
    if dd > -35:  return "🟠 경계"
    return "🔴 위험"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_close(ticker: str):
    try:
        hist = yf.Ticker(ticker).history(period="2y")
        if hist.empty:
            return None
        return hist["Close"]
    except:
        return None

def compute(close, mode_key):
    if close is None or len(close) == 0:
        return None
    current = float(close.iloc[-1])
    if mode_key == "52w":
        window = close.iloc[-252:] if len(close) >= 252 else close
        high = float(window.max())
    else:
        high = float(close.max())
    dd = (current - high) / high * 100
    diff = current - high  # 차액 (음수)
    return {"current": current, "high": high, "dd": dd, "diff": diff, "close": close}

# ─── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    mode = st.radio("기준 고점", ["52주 고점", "전고점(ATH)"])
    mode_key = "52w" if "52주" in mode else "ath"
    sort_by = st.selectbox("정렬", ["낙폭 심한 순", "낙폭 적은 순", "티커 알파벳순"])
    dd_filter = st.select_slider(
        "최소 낙폭 필터",
        options=[0, 5, 10, 15, 20, 30, 40, 50],
        value=0,
        format_func=lambda x: f"-{x}% 이상" if x > 0 else "전체 보기"
    )
    st.divider()
    st.markdown("**티커 추가**")
    extra_input = st.text_input("추가 티커 (쉼표 구분)", placeholder="예: UBER, SPOT")
    if "extra_tickers" not in st.session_state:
        st.session_state.extra_tickers = {}
    if st.button("➕ 추가", use_container_width=True) and extra_input:
        for t in extra_input.split(","):
            t = t.strip().upper()
            if t:
                st.session_state.extra_tickers[t] = t
        st.rerun()
    to_del = []
    for t in list(st.session_state.extra_tickers):
        c1, c2 = st.columns([3, 1])
        c1.write(t)
        if c2.button("✕", key=f"del_{t}"):
            to_del.append(t)
    for t in to_del:
        del st.session_state.extra_tickers[t]
    if to_del:
        st.rerun()
    st.divider()
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"갱신: {datetime.now().strftime('%H:%M:%S')} | 5분 캐시")

# ─── 데이터 로딩 ──────────────────────────────────────────────────────────────
combined = {**ALL_TICKERS, **st.session_state.extra_tickers}
all_results = {}
fail_list = []

prog = st.progress(0, text="📡 데이터 수신 중...")
ticker_list = list(combined.keys())
for i, ticker in enumerate(ticker_list):
    close = fetch_close(ticker)
    result = compute(close, mode_key)
    if result:
        result["name"] = combined[ticker]
        result["cat"] = TICKER_TO_CAT.get(ticker, "➕ 추가")
        all_results[ticker] = result
    else:
        fail_list.append(ticker)
    prog.progress((i + 1) / len(ticker_list), text=f"로딩 중... {ticker} ({i+1}/{len(ticker_list)})")
prog.empty()

if fail_list:
    st.warning(f"⚠️ 조회 실패: {', '.join(fail_list)}")

filtered = {k: v for k, v in all_results.items() if v["dd"] <= -dd_filter}

def sort_items(items):
    if sort_by == "낙폭 심한 순": return sorted(items, key=lambda x: x[1]["dd"])
    if sort_by == "낙폭 적은 순": return sorted(items, key=lambda x: -x[1]["dd"])
    return sorted(items, key=lambda x: x[0])

# ─── 헤더 & 요약 ─────────────────────────────────────────────────────────────
st.markdown("# 📉 DRAWDOWN MONITOR")
st.caption(f"기준: **{mode}** | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.divider()

if filtered:
    dds = [v["dd"] for v in filtered.values()]
    worst_t = min(filtered, key=lambda x: filtered[x]["dd"])
    best_t  = max(filtered, key=lambda x: filtered[x]["dd"])
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("📊 추적 종목",    f"{len(filtered)}개")
    m2.metric("📉 평균 낙폭",    f"{sum(dds)/len(dds):.1f}%")
    m3.metric("🔴 최대 낙폭",    f"{filtered[worst_t]['dd']:.1f}%", worst_t)
    m4.metric("🟢 최소 낙폭",    f"{filtered[best_t]['dd']:.1f}%",  best_t)
    m5.metric("🔴 위험 (>35%)", f"{sum(1 for d in dds if d <= -35)}개")
    m6.metric("🟡 주의 (>20%)", f"{sum(1 for d in dds if d <= -20)}개")

st.divider()

# ─── 전체 바 차트 ─────────────────────────────────────────────────────────────
with st.expander("📊 전체 낙폭 비교 차트", expanded=True):
    sorted_all = sort_items(list(filtered.items()))
    fig_bar = go.Figure(go.Bar(
        x=[k for k, _ in sorted_all],
        y=[v["dd"] for _, v in sorted_all],
        marker_color=[get_dd_color(v["dd"]) for _, v in sorted_all],
        text=[f"{v['dd']:.1f}%" for _, v in sorted_all],
        textposition="outside",
        customdata=[[v["name"], v["current"], v["high"]] for _, v in sorted_all],
        hovertemplate="<b>%{x}</b> — %{customdata[0]}<br>낙폭: <b>%{y:.2f}%</b><br>현재가: $%{customdata[1]:,.2f}<br>고점: $%{customdata[2]:,.2f}<extra></extra>",
    ))
    for lvl, col, lbl in [(-10,"#15803d","-10%"),(-20,"#b45309","-20%"),(-35,"#c2410c","-35%"),(-50,"#b91c1c","-50%")]:
        fig_bar.add_hline(y=lvl, line_dash="dot", line_color=col, line_width=1,
                          annotation_text=lbl, annotation_font_color=col, annotation_font_size=10)
    fig_bar.update_layout(
        height=420, margin=dict(t=20, b=10),
        yaxis=dict(title="낙폭 (%)", gridcolor="rgba(0,0,0,0.05)",
                   zeroline=True, zerolinecolor="rgba(0,0,0,0.2)"),
        xaxis=dict(tickfont=dict(size=10), tickangle=-45),
        bargap=0.2,
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="overview_bar")

# ─── 카드 렌더링 ─────────────────────────────────────────────────────────────
def render_cards(items, col_count=3):
    if not items:
        st.info("해당 조건의 종목이 없습니다.")
        return

    rows = [items[i:i+col_count] for i in range(0, len(items), col_count)]
    for row in rows:
        cols = st.columns(col_count)
        for ci, (ticker, data) in enumerate(row):
            dd    = data["dd"]
            color = get_dd_color(dd)
            bg    = get_dd_bg(dd)
            label = get_dd_label(dd)
            close = data["close"]

            with cols[ci]:
                # ── 컨테이너 (배경색 포함) ────────────────────────────────
                with st.container(border=True):
                    # ── 티커명 + 종목명 (항상 보이게 st.write 사용) ──────
                    st.write(f"**{ticker}** — {data['name']}")

                    # ── 낙폭 % (크게) ────────────────────────────────────
                    st.markdown(
                        f"<p style='font-size:36px;font-weight:900;color:{color};"
                        f"margin:0;padding:0;line-height:1.1'>{dd:.1f}% &nbsp;"
                        f"<span style='font-size:14px;font-weight:500'>{label}</span></p>",
                        unsafe_allow_html=True
                    )

                    # ── 낙폭 바 ─────────────────────────────────────────
                    pct = min(abs(dd), 100)
                    st.markdown(
                        f"<div style='height:8px;background:#e5e7eb;border-radius:4px;"
                        f"overflow:hidden;margin:6px 0 10px'>"
                        f"<div style='width:{pct:.1f}%;height:100%;background:{color};"
                        f"border-radius:4px'></div></div>",
                        unsafe_allow_html=True
                    )

                    # ── 수치 3개 ─────────────────────────────────────────
                    n1, n2, n3 = st.columns(3)
                    n1.metric("현재가",  f"${data['current']:,.2f}")
                    n2.metric("고점",    f"${data['high']:,.2f}")
                    n3.metric("차액",    f"${data['diff']:,.2f}")

                    # ── 차트 ────────────────────────────────────────────
                    hist_90 = close.iloc[-90:].rename("주가($)")
                    st.line_chart(hist_90, height=150, use_container_width=True, color=color)

# ─── 탭 렌더링 ───────────────────────────────────────────────────────────────
cat_names = list(CATEGORIES.keys())
tab_labels = ["📋 전체"] + cat_names
if st.session_state.extra_tickers:
    tab_labels.append("➕ 추가 티커")

tabs = st.tabs(tab_labels)

with tabs[0]:
    render_cards(sort_items(list(filtered.items())))

for i, (cat_name, cat_data) in enumerate(CATEGORIES.items()):
    with tabs[i + 1]:
        cat_items = sort_items([
            (t, all_results[t])
            for t in cat_data["tickers"]
            if t in all_results and all_results[t]["dd"] <= -dd_filter
        ])
        render_cards(cat_items)

if st.session_state.extra_tickers and len(tabs) > len(cat_names) + 1:
    with tabs[-1]:
        extra_items = sort_items([
            (t, all_results[t])
            for t in st.session_state.extra_tickers
            if t in all_results and all_results[t]["dd"] <= -dd_filter
        ])
        render_cards(extra_items)

# ─── 전체 테이블 ──────────────────────────────────────────────────────────────
st.divider()
with st.expander("📋 전체 데이터 테이블 & CSV 다운로드"):
    rows = []
    for cat_name, cat_data in CATEGORIES.items():
        for ticker in cat_data["tickers"]:
            if ticker in all_results:
                d = all_results[ticker]
                rows.append({
                    "카테고리":  cat_name,
                    "티커":      ticker,
                    "종목명":    d["name"],
                    "현재가($)": round(d["current"], 2),
                    "고점($)":   round(d["high"], 2),
                    "낙폭(%)":   round(d["dd"], 2),
                    "차액($)":   round(d["diff"], 2),
                    "단계":      get_dd_label(d["dd"]),
                })
    df = pd.DataFrame(rows).sort_values("낙폭(%)")
    st.dataframe(df, hide_index=True, use_container_width=True, height=400)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ CSV 다운로드", csv, "drawdown.csv", "text/csv", key="csv_dl")

st.caption("🟢 0~5% 양호 | 🟢 5~10% 안정 | 🟡 10~20% 주의 | 🟠 20~35% 경계 | 🔴 35%+ 위험 | 데이터: Yahoo Finance")
