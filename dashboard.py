
"""Ten integrated views. Private records are never stored in a shared Streamlit cache."""
import os,json,html
from pathlib import Path
import requests,pandas as pd,streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from app.schemas import DEPARTMENTS

load_dotenv()
st.set_page_config(
    page_title='CivicLens · Every voice matters',
    page_icon='🏛️',
    layout='wide',
    initial_sidebar_state='expanded'
)
API=os.getenv('API_URL','http://127.0.0.1:8000').rstrip('/')
TN_PLACES=json.loads((Path(__file__).resolve().parent/'config'/'tamil_nadu_places.json').read_text())

# Restore workspace selection after a browser refresh.
workspace_param = st.query_params.get("workspace", "")

if workspace_param in ("Citizen", "Official access"):
    st.session_state["workspace_entered"] = True
    st.session_state["access_mode"] = workspace_param

# Dedicated animated CivicLens welcome screen.
if not st.session_state.get("workspace_entered", False):

    # Global Streamlit styling: applies to the buttons and footnote below.
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,600;1,700&display=swap');

    .stApp {
      background:
        radial-gradient(ellipse at 82% 12%,rgba(244,113,94,.19),transparent 34%),
        radial-gradient(ellipse at 8% 88%,rgba(139,76,125,.19),transparent 38%),
        linear-gradient(135deg,#1d1722 0%,#30212f 56%,#211923 100%) !important;
      color:#fff1e9;
    }
    [data-testid="stHeader"] {background:transparent;}
    .block-container {max-width:1240px;padding-top:1.5rem;padding-bottom:2rem;}

    div.stButton > button {
      min-height:60px;
      width:100%;
      white-space:normal;
      border:1px solid rgba(255,179,138,.27);
      border-radius:16px;
      background:linear-gradient(120deg,rgba(74,46,62,.94),rgba(53,38,54,.96));
      color:#fff0e8;
      font-size:.98rem;
      font-weight:800;
      box-shadow:0 8px 25px rgba(0,0,0,.10);
      transition:transform .28s ease,box-shadow .28s ease,border-color .28s ease;
    }
    div.stButton > button:hover {
      transform:translateY(-4px);
      box-shadow:0 16px 35px rgba(240,91,67,.20);
      border-color:#ffb38a;
      color:#fff7f0;
    }
    .welcome-footnote {
      color:#c8afb9;
      text-align:center;
      font-size:.78rem;
      margin-top:20px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Render the entire animated illustration inside its own HTML frame.
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,600;1,700&display=swap');

    * {box-sizing:border-box}
    html,body {
      margin:0;
      padding:0;
      background:transparent;
      color:#fff1e9;
      font-family:'DM Sans',sans-serif;
      overflow:hidden;
    }
    .welcome-wrap {
      position:relative;
      isolation:isolate;
      overflow:hidden;
      display:grid;
      grid-template-columns:1.08fr .92fr;
      align-items:center;
      gap:20px;
      min-height:470px;
      padding:clamp(26px,4vw,54px);
      border:1px solid rgba(255,179,138,.25);
      border-radius:30px;
      background:linear-gradient(125deg,#2f2130,#4e2b3b);
      box-shadow:0 25px 65px rgba(0,0,0,.22);
      animation:cl-appear .85s cubic-bezier(.2,.7,.2,1) both;
    }
    .welcome-wrap:before {
      content:"";
      position:absolute;
      z-index:-1;
      width:440px;height:440px;
      right:0;top:-240px;border-radius:50%;
      background:radial-gradient(circle,rgba(255,177,138,.34),rgba(240,91,67,.09) 48%,transparent 72%);
      animation:cl-glow 8s ease-in-out infinite;
    }
    .welcome-wrap:after {
      content:"";
      position:absolute;
      z-index:-1;
      width:280px;height:280px;
      left:22%;bottom:-230px;border-radius:50%;
      background:rgba(201,92,114,.19);
      filter:blur(55px);
      animation:cl-glow 11s ease-in-out infinite reverse;
    }
    .welcome-copy {position:relative;z-index:2;min-width:0}
    .welcome-kicker {
      display:inline-flex;align-items:center;gap:9px;
      color:#ffb38a;font-size:.72rem;font-weight:800;
      letter-spacing:.16em;text-transform:uppercase;
      animation:cl-rise .7s .12s both;
    }
    .welcome-kicker:before {
      content:"";display:inline-block;width:24px;height:2px;
      background:#ff9e7c;border-radius:5px;
      box-shadow:0 0 12px rgba(255,158,124,.6);
    }
    .welcome-title {
      margin:22px 0 18px;color:#fff4ec;
      font-family:'Playfair Display',Georgia,serif;
      font-size:clamp(2.4rem,4.6vw,4.2rem);
      line-height:1.08;letter-spacing:-.055em;
      animation:cl-title-in 1s .18s both;
    }
    .welcome-title em {
      display:block;color:#ffad8e;font-weight:600;
      text-shadow:0 0 34px rgba(255,137,116,.10);
    }
    .welcome-description {
      max-width:520px;color:#e9d2d6;
      font-size:1rem;line-height:1.8;
      animation:cl-rise .8s .38s both;
    }
    .welcome-tags {
      display:flex;flex-wrap:wrap;gap:8px;
      margin-top:20px;animation:cl-rise .8s .52s both;
    }
    .welcome-tag {
      padding:7px 11px;border-radius:999px;
      border:1px solid rgba(255,179,138,.23);
      background:rgba(31,23,34,.48);color:#ffe1d4;
      font-size:.76rem;font-weight:700;
      transition:background .25s ease,border-color .25s ease,transform .25s ease;
    }
    .welcome-tag:hover {
      transform:translateY(-3px);
      background:rgba(240,113,94,.16);
      border-color:rgba(255,179,138,.65);
    }
    .welcome-art {
      position:relative;min-width:0;
      animation:cl-art-in 1.15s .2s both;
    }
    .welcome-art:before {
      content:"";position:absolute;width:75%;aspect-ratio:1;
      left:12%;top:8%;border-radius:50%;
      background:rgba(242,121,98,.15);filter:blur(42px);
      animation:cl-glow 7s ease-in-out infinite;
    }
    .welcome-city {
      position:relative;display:block;width:100%;height:auto;
      overflow:visible;filter:drop-shadow(0 15px 26px rgba(0,0,0,.16));
    }
    .city-buildings {
      transform-origin:50% 100%;
      animation:cl-city-float 8s ease-in-out infinite;
    }
    .city-cloud {animation:cl-cloud 15s ease-in-out infinite}
    .city-cloud.delay {animation-delay:-7s}
    .city-particles {
      transform-box:fill-box;transform-origin:center;
      animation:cl-particles 5s ease-in-out infinite;
    }
    .city-particles.delay {animation-delay:-2.5s}

    @keyframes cl-appear {
      from {opacity:0;transform:translateY(18px) scale(.99);filter:blur(5px)}
      to {opacity:1;transform:translateY(0) scale(1);filter:blur(0)}
    }
    @keyframes cl-rise {
      from {opacity:0;transform:translateY(18px)}
      to {opacity:1;transform:translateY(0)}
    }
    @keyframes cl-title-in {
      from {opacity:0;transform:translateY(24px);filter:blur(7px)}
      to {opacity:1;transform:translateY(0);filter:blur(0)}
    }
    @keyframes cl-art-in {
      from {opacity:0;transform:translateX(28px) scale(.96);filter:blur(5px)}
      to {opacity:1;transform:translateX(0) scale(1);filter:blur(0)}
    }
    @keyframes cl-glow {
      0%,100% {transform:scale(.92);opacity:.65}
      50% {transform:scale(1.1);opacity:1}
    }
    @keyframes cl-city-float {
      0%,100% {transform:translateY(0)}
      50% {transform:translateY(-9px)}
    }
    @keyframes cl-cloud {
      0%,100% {transform:translateX(0)}
      50% {transform:translateX(13px)}
    }
    @keyframes cl-particles {
      0%,100% {opacity:.35;transform:translateY(5px) scale(.85)}
      50% {opacity:1;transform:translateY(-9px) scale(1.15)}
    }
    @media(max-width:820px) {
      .welcome-wrap {grid-template-columns:1fr;min-height:0;gap:4px;padding:27px;border-radius:23px}
      .welcome-title {font-size:clamp(2.5rem,8vw,3.6rem)}
      .welcome-art {max-width:400px;width:100%;margin:0 auto}
      .welcome-description {font-size:.95rem}
    }
    @media(max-width:480px) {
      .welcome-wrap {padding:22px 19px}
      .welcome-title {font-size:2.4rem}
      .welcome-kicker {font-size:.65rem;letter-spacing:.12em}
      .welcome-tags {gap:6px}
      .welcome-tag {font-size:.7rem;padding:6px 9px}
    }
    @media(prefers-reduced-motion:reduce) {
      *,*:before,*:after {animation:none!important;transition:none!important}
    }

    /* CivicLens — subtle internal-page interactions */

    /* Gentle lift for dashboard statistics and custom content cards */
    [data-testid="stMetric"],
    .cl-chart-card,
    .cl-voice-shell {
    	transition: transform 0.22s ease, box-shadow 0.22s ease,
                    border-color 0.22s ease;
    }

     .cl-chart-card:hover,
.cl-voice-shell:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 26px rgba(115, 60, 39, 0.10);
    border-color: rgba(240, 91, 67, 0.34);
}

/* Smooth form focus and button interactions */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
[data-baseweb="select"] > div,
.stButton > button {
    transition: border-color 0.2s ease, box-shadow 0.2s ease,
                background-color 0.2s ease;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus {
    border-color: #f05b43 !important;
    box-shadow: 0 0 0 3px rgba(240, 91, 67, 0.13) !important;
}

/* Keep headings readable on narrow screens */
h1, h2, h3,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    overflow-wrap: anywhere;
}

/* Accessible: minimize movement when requested */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
    }
}

    </style>
    </head>
    <body>
    <section class="welcome-wrap">
      <div class="welcome-copy">
        <div class="welcome-kicker">CivicLens · Citizen-first civic care</div>
        <div class="welcome-title">Every voice.<em>A clearer path to resolution.</em></div>
        <div class="welcome-description">
          Your concerns deserve to be heard. Raise a civic grievance in Tamil,
          Hindi, English and more, and help route it to the right team for human review.
        </div>
        <div class="welcome-tags">
          <span class="welcome-tag">தமிழ் · Tamil</span>
          <span class="welcome-tag">हिन्दी · Hindi</span>
          <span class="welcome-tag">English</span>
          <span class="welcome-tag">✦ AI-assisted routing</span>
        </div>
      </div>
      <div class="welcome-art">
        <svg class="welcome-city" viewBox="0 0 560 450" role="img"
             aria-label="Stylized city at sunrise" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="cl-building" x1="0" y1="0" x2="1" y2="1">
              <stop stop-color="#ffbd9c"/><stop offset="1" stop-color="#bb655f"/>
            </linearGradient>
            <linearGradient id="cl-ground" x1="0" y1="0" x2="0" y2="1">
              <stop stop-color="#a95765" stop-opacity=".7"/><stop offset="1" stop-color="#38263d" stop-opacity=".1"/>
            </linearGradient>
          </defs>
          <circle cx="340" cy="142" r="100" fill="#f27669" opacity=".09"/>
          <circle cx="340" cy="142" r="72" fill="#ffb38a" opacity=".12"/>
          <circle cx="340" cy="142" r="52" fill="#ffc49e" opacity=".65"/>
          <g class="city-cloud" fill="none" stroke="#f8a78c" stroke-width="3" stroke-linecap="round" opacity=".75">
            <path d="M70 120q12 -13 24 0q12 -13 24 0"/>
            <path d="M390 90q10 -11 20 0q10 -11 20 0"/>
          </g>
          <g class="city-cloud delay" fill="none" stroke="#f8a78c" stroke-width="3" stroke-linecap="round" opacity=".55">
            <path d="M110 170q10 -11 20 0q10 -11 20 0"/>
            <path d="M420 188q12 -13 24 0q12 -13 24 0"/>
          </g>
          <path d="M20 356Q150 316 275 353T540 338V420H20Z" fill="url(#cl-ground)"/>
          <g class="city-buildings" fill="url(#cl-building)" stroke="#f8b195" stroke-opacity=".35" stroke-width="1.5">
            <path d="M42 365V245H66V220L90 187L114 220V245H138V365Z"/>
            <path d="M63 272H117M63 301H117M63 330H117" fill="none" stroke="#6f3b4c" stroke-opacity=".48"/>
            <path d="M151 365V271H173V238H194V212H215V238H236V271H258V365Z"/>
            <path d="M171 289H238M171 319H238" fill="none" stroke="#6f3b4c" stroke-opacity=".48"/>
            <path d="M267 365V263Q267 205 315 188Q363 205 363 263V365Z"/>
            <path d="M280 365V265Q280 221 315 207Q350 221 350 265V365" fill="none" stroke="#6f3b4c" stroke-opacity=".38"/>
            <path d="M300 190L315 157L330 190Z"/>
            <path d="M379 365V270H398V240H419V210H440V240H461V270H480V365Z"/>
            <path d="M397 291H462M397 321H462" fill="none" stroke="#6f3b4c" stroke-opacity=".48"/>
            <path d="M20 365Q160 346 280 366T540 355V390Q280 410 20 390Z" opacity=".52"/>
          </g>
          <path d="M20 367Q150 344 280 367T540 355" fill="none" stroke="#ffc19e" stroke-opacity=".65" stroke-width="2"/>
          <g class="city-particles" fill="#ffcfb1">
            <circle cx="80" cy="145" r="2"/><circle cx="454" cy="132" r="2"/>
            <circle cx="480" cy="224" r="2"/><circle cx="180" cy="167" r="2"/>
          </g>
          <g class="city-particles delay" fill="#ffe0bd">
            <circle cx="130" cy="235" r="1.8"/><circle cx="425" cy="270" r="2"/>
            <circle cx="235" cy="125" r="1.6"/><circle cx="505" cy="170" r="1.7"/>
          </g>
        </svg>
      </div>
    </section>
    </body>
    </html>
    """, height=560, scrolling=False)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    citizen_col, official_col = st.columns(2, gap="large")

    with citizen_col:
        st.markdown("### 🙋 Citizen space")
        st.caption("Raise a concern or track an existing grievance.")
        if st.button("Continue as Citizen  →", type="primary",
                     key="welcome_citizen", use_container_width=True):
            st.session_state["workspace_entered"] = True
            st.session_state["access_mode"] = "Citizen"
            st.query_params["workspace"] = "Citizen"
            st.rerun()

    with official_col:
        st.markdown("### 🏛️ Official access")
        st.caption("Secure sign-in for authorized staff only.")
        if st.button("Sign in as an Official  →",
                     key="welcome_official", use_container_width=True):
            st.session_state["workspace_entered"] = True
            st.session_state["access_mode"] = "Official access"
            st.query_params["workspace"] = "Official access"
            st.rerun()

    st.markdown(
        "<div class='welcome-footnote'>CivicLens demonstration · Official tools require backend authorization</div>",
        unsafe_allow_html=True
    )
    st.stop()
        
st.markdown(r'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');
:root{--cl-cream:#fff8f0;--cl-peach:#ffb38a;--cl-coral:#f05b43;--cl-terracotta:#c4663d;--cl-clay:#733c27;--cl-ink:#242321;--cl-muted:#776b62;}
.stApp{background:radial-gradient(ellipse at 92% 4%,rgba(255,179,138,.18),transparent 32%),linear-gradient(135deg,#fffaf4 0%,#fff8f0 48%,#fffdf9 100%);color:var(--cl-ink);font-family:'DM Sans',sans-serif;}
.block-container{max-width:1450px;padding-top:1.15rem;padding-bottom:3rem;}
[data-testid="stHeader"]{background:rgba(255,248,240,.78);backdrop-filter:blur(14px)}
h1{font-size:clamp(2rem,4vw,3.25rem)!important;line-height:1.08!important}
h2{font-size:clamp(1.45rem,2.5vw,2rem)!important}
p,li,label{line-height:1.65}
.stButton>button{border:1px solid rgba(196,102,61,.35);border-radius:999px;background:linear-gradient(115deg,#f05b43,#df7447);color:white;font-weight:700;padding:.58rem 1.15rem;box-shadow:0 7px 18px rgba(240,91,67,.16);transition:transform .22s ease,box-shadow .22s ease,filter .22s ease}
.stButton>button:hover{transform:translateY(-2px);box-shadow:0 12px 24px rgba(196,102,61,.24);filter:saturate(1.08);border-color:#c4663d;color:white}
.stTextInput input,.stTextArea textarea,.stNumberInput input,[data-baseweb="select"]>div{border-radius:12px!important;border-color:rgba(115,60,39,.2)!important;background:rgba(255,255,255,.78)!important}
.stTextInput input:focus,.stTextArea textarea:focus{box-shadow:0 0 0 3px rgba(240,91,67,.12)!important}
[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(255,255,255,.95),rgba(255,238,224,.74));border:1px solid rgba(196,102,61,.18);border-radius:18px;padding:16px 18px;box-shadow:0 8px 24px rgba(115,60,39,.045);transition:transform .25s ease,box-shadow .25s ease}
[data-testid="stMetric"]:hover{transform:translateY(-3px);box-shadow:0 12px 28px rgba(115,60,39,.09)}
[data-testid="stExpander"]{border:1px solid rgba(196,102,61,.18);border-radius:14px;background:rgba(255,255,255,.48)}
[data-testid="stAlert"]{border-radius:14px}
[data-testid="stDataFrame"], [data-testid="stTable"]{border:1px solid rgba(196,102,61,.15);border-radius:14px;overflow:hidden}
.cl-hero{position:relative;overflow:hidden;border:1px solid rgba(196,102,61,.17);border-radius:26px;padding:clamp(24px,4vw,48px);margin:0 0 1.35rem;background:linear-gradient(110deg,rgba(255,255,255,.92) 0%,rgba(255,246,236,.96) 54%,rgba(255,218,194,.78) 100%);box-shadow:0 18px 48px rgba(115,60,39,.07);isolation:isolate}
.cl-hero:before{content:'';position:absolute;z-index:-1;width:440px;height:440px;right:-90px;top:-220px;border-radius:50%;background:radial-gradient(circle,rgba(255,179,138,.58),rgba(240,91,67,.08) 63%,transparent 70%);animation:cl-float 10s ease-in-out infinite}
.cl-hero:after{content:'';position:absolute;z-index:-1;width:360px;height:140px;right:5%;bottom:-88px;border-radius:50%;background:rgba(196,102,61,.12);filter:blur(20px)}.cl-landmark{position:absolute;z-index:-1;right:1.5%;bottom:0;width:min(48%,620px);height:auto;opacity:.3;filter:drop-shadow(0 12px 22px rgba(115,60,39,.08));animation:cl-landmark-drift 12s ease-in-out infinite}.cl-landmark path,.cl-landmark rect,.cl-landmark circle{vector-effect:non-scaling-stroke}.cl-sunset{transform-origin:552px 92px;animation:cl-sun-glow 7s ease-in-out infinite}@keyframes cl-sun-glow{0%,100%{opacity:.22;transform:scale(.96)}50%{opacity:.42;transform:scale(1.08)}}@keyframes cl-landmark-drift{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
.cl-eyebrow{font-size:.72rem;letter-spacing:.19em;text-transform:uppercase;font-weight:800;color:#a64d32;margin-bottom:12px}.cl-headline{font-family:'Playfair Display',Georgia,serif;font-size:clamp(2.1rem,4.8vw,4rem);letter-spacing:-.055em;line-height:1.02;color:#242321;max-width:850px;position:relative;z-index:1}.cl-hero .cl-eyebrow,.cl-hero .cl-sub,.cl-hero .cl-tags{position:relative;z-index:1}.cl-headline em{font-weight:600;color:#e86643}.cl-sub{font-size:1rem;color:#756258;max-width:780px;margin-top:16px}.cl-tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}.cl-tag{border:1px solid rgba(196,102,61,.23);background:rgba(255,255,255,.72);border-radius:999px;padding:7px 12px;color:#6e4534;font-size:.78rem;font-weight:700}.cl-ticker{display:grid;grid-template-columns:max-content minmax(0,1fr);align-items:center;gap:16px;overflow:hidden;white-space:nowrap;border:1px solid rgba(196,102,61,.2);border-radius:14px;padding:12px 16px;margin:0 0 1.6rem;background:linear-gradient(90deg,rgba(255,228,210,.9),rgba(255,249,242,.95));color:#78503e;font-size:.82rem}.cl-ticker strong{color:#b34f34;flex:0 0 auto;position:relative;z-index:1}.cl-ticker-track{display:block;min-width:0;overflow:hidden;animation:cl-marquee 32s linear infinite;position:relative}.cl-ticker:hover .cl-ticker-track{animation-play-state:paused}.cl-section-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.15em;color:#b35c3e;font-weight:800}.cl-voice-shell{padding:20px;border-radius:22px;background:linear-gradient(135deg,rgba(255,255,255,.92),rgba(255,235,220,.85));border:1px solid rgba(196,102,61,.2)}.cl-chart-card{border:1px solid rgba(196,102,61,.17);border-radius:16px;background:rgba(255,255,255,.65);padding:14px 16px;margin:8px 0 14px}.cl-chart-row{display:grid;grid-template-columns:minmax(90px,34%) 1fr 34px;align-items:center;gap:10px;margin:10px 0;font-size:.78rem;color:#6c5143}.cl-chart-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.cl-chart-track{height:10px;background:#f4e3d8;border-radius:99px;overflow:hidden}.cl-chart-fill{height:100%;width:var(--bar-width);border-radius:99px;background:linear-gradient(90deg,#ffb38a,#f05b43,#c4663d);transform-origin:left;animation:cl-bar-in .95s cubic-bezier(.2,.75,.2,1) both}.cl-chart-value{text-align:right;font-weight:800;color:#733c27;font-variant-numeric:tabular-nums}@keyframes cl-bar-in{from{transform:scaleX(.02);opacity:.35}to{transform:scaleX(1);opacity:1}}.cl-wave{height:52px;display:flex;align-items:center;justify-content:center;gap:4px;margin:8px auto 14px}.cl-wave span{width:4px;border-radius:8px;background:linear-gradient(180deg,#ffb38a,#f05b43);animation:cl-wave 1.05s ease-in-out infinite;animation-play-state:paused}.cl-wave.is-live span{animation-play-state:running}.cl-wave span:nth-child(5n+1){height:14px;animation-delay:-.6s}.cl-wave span:nth-child(5n+2){height:28px;animation-delay:-.3s}.cl-wave span:nth-child(5n+3){height:42px;animation-delay:-.8s}.cl-wave span:nth-child(5n+4){height:22px;animation-delay:-.1s}.cl-wave span:nth-child(5n){height:34px;animation-delay:-.45s}
@keyframes cl-float{0%,100%{transform:translate(0,0)}50%{transform:translate(-22px,18px)}}@keyframes cl-wave{0%,100%{transform:scaleY(.48);opacity:.55}50%{transform:scaleY(1.05);opacity:1}}@keyframes cl-marquee{0%{transform:translateX(0)}100%{transform:translateX(-38%)}}
@media(max-width:700px){.cl-hero{border-radius:18px;padding:22px}.cl-headline{font-size:2.35rem}.cl-ticker{gap:8px}.cl-sub{font-size:.92rem}.cl-landmark{width:75%;right:-8%;opacity:.12}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.01ms!important}}

/* CivicLens Updates: contained animated ticker */
.cl-ticker {
    display: grid;
    grid-template-columns: max-content minmax(0, 1fr);
    align-items: center;
    gap: 12px;
    width: 100%;
    min-width: 0;
    box-sizing: border-box;
    overflow: hidden;
    white-space: nowrap;
}
.cl-ticker strong {
    display: block;
    position: relative;
    z-index: 2;
    white-space: nowrap;
}
.cl-ticker-track {
    display: block;
    width: 100%;
    min-width: 0;
    overflow: hidden;
    white-space: nowrap;
    overflow-wrap: normal;
    animation: cl-marquee 24s linear infinite !important;
    will-change: transform;
}
.cl-ticker:hover .cl-ticker-track {
    animation-play-state: paused;
}
@media (max-width: 700px) {
    .cl-ticker {
        grid-template-columns: minmax(0, 1fr);
        align-items: start;
        gap: 8px;
        padding: 12px;
        white-space: normal;
    }
    .cl-ticker strong {
        white-space: normal;
    }
    .cl-ticker-track {
        white-space: nowrap;
        animation-duration: 32s !important;
    }
}
@media (prefers-reduced-motion: reduce) {
    .cl-ticker-track {
        animation: none !important;
        white-space: normal;
    }
}


/* CivicLens ticker final overlap repair */
.cl-ticker {
    display: block !important;
    position: relative;
    width: 100%;
    min-width: 0;
    box-sizing: border-box;
    overflow: hidden !important;
    white-space: nowrap !important;
    isolation: isolate;
    min-height: 46px;
    padding: 12px 16px 12px 190px !important;
}
.cl-ticker strong {
    position: absolute !important;
    left: 16px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 3;
    white-space: nowrap !important;
    background: #382838;
    padding: 4px 6px;
    border-radius: 5px;
}
.cl-ticker-track {
    display: block !important;
    width: max-content !important;
    max-width: none !important;
    min-width: max-content !important;
    overflow: visible !important;
    white-space: nowrap !important;
    animation: cl-ticker-safe-scroll 28s linear infinite !important;
    will-change: transform;
}
.cl-ticker:hover .cl-ticker-track {
    animation-play-state: paused !important;
}
@keyframes cl-ticker-safe-scroll {
    from { transform: translateX(0); }
    to   { transform: translateX(-38%); }
}
@media (max-width: 700px) {
    .cl-ticker {
        padding: 12px !important;
        min-height: 0;
        white-space: normal !important;
    }
    .cl-ticker strong {
        position: static !important;
        display: block;
        width: fit-content;
        transform: none;
        margin-bottom: 8px;
    }
    .cl-ticker-track {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        animation: none !important;
    }
}
@media (prefers-reduced-motion: reduce) {
    .cl-ticker-track { animation: none !important; }
}

</style>''',unsafe_allow_html=True)
st.markdown('''<section class="cl-hero"><svg class="cl-landmark" viewBox="0 0 680 330" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="cl-land" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ffb38a"/><stop offset="1" stop-color="#c4663d"/></linearGradient></defs><circle class="cl-sunset" cx="552" cy="92" r="48" fill="#f05b43" opacity=".30"/><circle cx="552" cy="92" r="34" fill="#ffb38a" opacity=".48"/><path d="M0 292 Q150 265 285 294 T680 282 V330 H0Z" fill="#ffb38a" opacity=".6"/><path d="M18 294 Q145 281 285 300 T680 290" fill="none" stroke="#c4663d" stroke-width="3" opacity=".6"/><g fill="url(#cl-land)" stroke="#a95235" stroke-width="1.5"><path d="M60 260 V174 H77 V145 L95 120 L113 145 V174 H130 V260Z"/><path d="M73 174 H117 M69 196 H121 M66 220 H124" fill="none"/><path d="M145 260 V190 H166 V162 H183 V137 H201 V162 H218 V190 H239 V260Z"/><path d="M160 190 Q191 146 223 190" fill="none"/><path d="M270 260 V192 Q270 143 319 132 Q368 143 368 192 V260Z"/><path d="M283 260 V194 Q283 157 319 149 Q355 157 355 194 V260" fill="none"/><path d="M302 132 Q319 105 336 132 L319 92Z"/><path d="M405 260 V185 H421 V155 H437 V127 H453 V155 H469 V185 H485 V260Z"/><path d="M418 185 H472 M414 211 H476" fill="none"/><path d="M520 260 V198 H536 V176 H553 V150 H570 V176 H587 V198 H603 V260Z"/><path d="M532 198 H591 M527 224 H597" fill="none"/></g><g fill="#733c27" opacity=".45"><rect x="0" y="260" width="680" height="5"/><circle cx="35" cy="240" r="18"/><circle cx="45" cy="226" r="15"/><circle cx="628" cy="236" r="22"/><circle cx="646" cy="219" r="18"/></g><g fill="none" stroke="#c4663d" stroke-width="2" stroke-linecap="round"><path d="M395 65 q8 -9 16 0 q-8 -3 -16 0"/><path d="M420 49 q7 -8 14 0 q-7 -3 -14 0"/><path d="M382 86 q7 -8 14 0 q-7 -3 -14 0"/></g></svg><div class="cl-eyebrow">Multilingual · AI-powered · Citizen-first</div><div class="cl-headline">Every voice.<br><em>A clearer path to resolution.</em></div><div class="cl-sub">CivicLens helps citizens raise grievances in Tamil, Hindi, English and more — using AI to understand, classify and route concerns for faster human review.</div><div class="cl-tags"><span class="cl-tag">தமிழ் · Tamil</span><span class="cl-tag">हिन्दी · Hindi</span><span class="cl-tag">English</span><span class="cl-tag">✦ Local-first processing</span></div></section><div class="cl-ticker"><strong>✦ CIVICLENS UPDATES</strong><span class="cl-ticker-track">Every voice matters　 •　 Multilingual grievance support　 •　 Clearer routing, better accountability　 •　 Citizens first, always　 •　 Every voice matters　 •　 Multilingual grievance support　 •　 Clearer routing, better accountability　 •　 Citizens first, always　 •　</span></div>''',unsafe_allow_html=True)
st.sidebar.markdown('''<div style="padding:8px 0 18px"><div style="font-size:1.45rem;font-weight:800;color:#733c27;letter-spacing:-.04em">◈ CivicLens<span style="color:#f05b43">.</span></div><div style="font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;color:#9b6b55">Every voice matters</div></div>''',unsafe_allow_html=True)
theme_mode=st.sidebar.toggle('🌙 Dark mode',value=True,help='Switch between warm light and plum-night themes.')
if theme_mode:
    st.markdown('''<style>
.stApp{background:radial-gradient(ellipse at 90% 0%,rgba(240,91,67,.16),transparent 34%),linear-gradient(135deg,#211923 0%,#2b202d 52%,#241b28 100%)!important;color:#fff1e9!important}
[data-testid="stHeader"]{background:rgba(33,25,35,.86)!important}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#352536 0%,#29202d 55%,#211923 100%)!important;border-right:1px solid rgba(255,179,138,.18)!important}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#f2d9ce!important}
h1,h2,h3,[data-testid="stMarkdownContainer"],p,li,label,.stCaption{color:#fff0e8}
.cl-hero{background:linear-gradient(115deg,rgba(57,39,55,.97),rgba(76,43,55,.94) 55%,rgba(117,55,60,.86))!important;border-color:rgba(255,179,138,.24)!important;box-shadow:0 18px 48px rgba(0,0,0,.18)!important}
.cl-headline{color:#fff4ec!important}.cl-headline em{color:#ffad8e!important}.cl-sub{color:#f1d4c7!important}.cl-eyebrow,.cl-section-label{color:#ffb38a!important}
.cl-tag{background:rgba(45,31,43,.78)!important;color:#ffe4d6!important;border-color:rgba(255,179,138,.26)!important}
.cl-ticker{background:linear-gradient(90deg,#382838,#4a2d3a)!important;color:#ffe5d8!important;border-color:rgba(255,179,138,.2)!important}.cl-ticker strong{color:#ffb38a!important}
.cl-voice-shell,.cl-chart-card{background:linear-gradient(135deg,rgba(55,40,53,.96),rgba(72,43,53,.92))!important;border-color:rgba(255,179,138,.2)!important}.cl-chart-row{color:#f2d9ce!important}.cl-chart-track{background:#4a3948!important}.cl-chart-value{color:#ffd0b8!important}
[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(63,45,60,.96),rgba(78,47,57,.88))!important;border-color:rgba(255,179,138,.2)!important}[data-testid="stMetric"] label,[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#fff0e8!important}
.stTextInput input,.stTextArea textarea,.stNumberInput input,[data-baseweb="select"]>div{background:#342735!important;color:#fff0e8!important;border-color:rgba(255,179,138,.28)!important}
[data-testid="stExpander"]{background:rgba(55,40,53,.72)!important;border-color:rgba(255,179,138,.2)!important}[data-testid="stDataFrame"],[data-testid="stTable"]{border-color:rgba(255,179,138,.2)!important}
</style>''',unsafe_allow_html=True)
st.markdown(r'''<style>
/* CivicLens motion polish: subtle chart, metric and content transitions. */
@keyframes cl-card-enter{from{opacity:0;transform:translateY(12px) scale(.99)}to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes cl-metric-enter{0%{opacity:.35;transform:translateY(8px)}100%{opacity:1;transform:translateY(0)}}
@keyframes cl-chart-sheen{0%{transform:translateX(-160%);opacity:0}18%{opacity:.55}65%{opacity:.2}100%{transform:translateX(260%);opacity:0}}
@keyframes cl-live-pulse{0%,100%{box-shadow:0 0 0 0 rgba(240,91,67,.2)}50%{box-shadow:0 0 0 5px rgba(240,91,67,0)}}
.cl-chart-card{position:relative;overflow:hidden;animation:cl-card-enter .58s cubic-bezier(.2,.75,.2,1) both;transition:transform .25s ease,box-shadow .25s ease,border-color .25s ease}
.cl-chart-card:before{content:'';position:absolute;top:0;bottom:0;left:0;width:28%;pointer-events:none;background:linear-gradient(100deg,transparent,rgba(255,179,138,.15),transparent);transform:translateX(-160%);animation:cl-chart-sheen 1.8s .35s ease-out both}
.cl-chart-card:hover{transform:translateY(-3px);box-shadow:0 15px 32px rgba(115,60,39,.13);border-color:rgba(240,91,67,.38)}
.cl-chart-row{position:relative;animation:cl-card-enter .45s ease both;transition:transform .2s ease}
.cl-chart-row:hover{transform:translateX(3px)}
.cl-chart-track{box-shadow:inset 0 1px 2px rgba(80,40,30,.06)}
.cl-chart-fill{position:relative;overflow:hidden;box-shadow:0 0 10px rgba(240,91,67,.12);animation:cl-bar-in 1.05s cubic-bezier(.2,.75,.2,1) both}
.cl-chart-fill:after{content:'';position:absolute;inset:0;width:45%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.48),transparent);transform:translateX(-150%);animation:cl-chart-sheen 1.6s .5s ease-out both}
[data-testid="stMetric"]{animation:cl-metric-enter .5s ease both;position:relative;overflow:hidden}
[data-testid="stMetric"]:hover{transform:translateY(-4px) scale(1.008)!important;box-shadow:0 15px 32px rgba(115,60,39,.13)!important}
[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"], [data-testid="stPlotlyChart"]{animation:cl-card-enter .65s ease both;transition:filter .25s ease}
[data-testid="stVegaLiteChart"]:hover,[data-testid="stPlotlyChart"]:hover{filter:drop-shadow(0 5px 10px rgba(115,60,39,.09))}
.cl-live-dot{display:inline-block;width:7px;height:7px;margin:0 7px 1px 0;border-radius:50%;background:#f05b43;animation:cl-live-pulse 2s ease-in-out infinite;vertical-align:middle}
@media(prefers-reduced-motion:reduce){.cl-chart-card,.cl-chart-card:before,.cl-chart-row,.cl-chart-fill,.cl-chart-fill:after,[data-testid="stMetric"],[data-testid="stVegaLiteChart"],[data-testid="stPlotlyChart"],.cl-live-dot{animation:none!important;transition:none!important}.cl-chart-card:hover,.cl-chart-row:hover,[data-testid="stMetric"]:hover{transform:none!important}}
</style>''',unsafe_allow_html=True)

views=['Citizen grievance submission','Voice grievance upload','Complaint tracking','Department priority queue','Emergency grievance management','Duplicate complaint review','Analytics dashboard','NLP prediction explanations','Human feedback and reassignment','System health and model information']

access_mode = st.session_state.get("access_mode", "Citizen")
if st.sidebar.button("← Back to welcome page", use_container_width=True):
    st.session_state["workspace_entered"] = False
    st.session_state.pop("official_token", None)
    st.session_state.pop("official_token_input", None)
    st.query_params.clear()
    st.rerun()

token=st.session_state.get('official_token','') if access_mode=='Official access' else ''

if access_mode=='Official access':
    if token:
        st.sidebar.success('Official session active')
        if st.sidebar.button('Sign out of official access'):
            st.session_state.pop('official_token',None)
            st.rerun()
    else:
        st.sidebar.caption('OFFICIAL SIGN-IN')
        candidate=st.sidebar.text_input(
            'Official access token',
            type='password',
            key='official_token_input',
            help='Use the ADMIN_TOKEN configured on the backend. Never share it with citizens.'
        )
        if st.sidebar.button('Sign in securely',type='primary'):
            if not candidate:
                st.sidebar.warning('Enter your official access token.')
            else:
                try:
                    response=requests.get(
                        API+'/api/v1/system',
                        headers={'Authorization':'Bearer '+candidate},
                        timeout=10
                    )
                    if response.ok:
                        st.session_state['official_token']=candidate
                        st.rerun()
                    elif response.status_code==503:
                        st.sidebar.error('Official access is not configured correctly on the backend.')
                    else:
                        st.sidebar.error('Access denied. Check your official token.')
                except requests.RequestException:
                    st.sidebar.error('Cannot reach the backend. Check that FastAPI is running.')
        st.info('Official management tools are locked until the backend verifies your access.')
        st.stop()

citizen_views=[views[0],views[1],views[2],views[7]]
official_views=views[3:7]+views[8:10]
view=st.sidebar.radio(
    'Workspace',
    citizen_views if access_mode=='Citizen' else official_views
)
st.sidebar.caption(
    'Private records require a complaint tracking token or official authorization. '
    'Demonstration routing is not a government integration.'
)

def call(method,path,tracking=None,**kwargs):
    headers={}
    if token:headers['Authorization']='Bearer '+token
    if tracking:headers['X-Tracking-Token']=tracking
    try:
        with st.spinner('Connecting securely to CivicLens…'):
            response=requests.request(method,API+path,headers=headers,timeout=180 if 'audio' in path else 30,**kwargs)
        if not response.ok:
            try:detail=response.json().get('detail','Request failed')
            except ValueError:detail='Backend returned an invalid response'
            st.error(f'{response.status_code}: {detail}')
            if response.status_code==503:st.info('Check that optional local models are installed and configured, then restart the backend.')
            return None
        return response.json()
    except requests.RequestException:st.error('Cannot reach the backend. Check that FastAPI is running.');return None

def location(prefix, require_district_place=False):
    st.caption('Choose the Tamil Nadu district and a city, town, or local area. The place list updates with the district. Legacy municipality/ward fields remain available for detailed routing.')
    a,b=st.columns(2)
    district_options=['Select a district']+sorted(TN_PLACES)
    district_label=a.selectbox('Select District',district_options,key=prefix+'district')
    district='' if district_label=='Select a district' else district_label
    place_options=['Select a place']+TN_PLACES.get(district,[])
    place_label=b.selectbox('Select Place',place_options,key=prefix+'place')
    place='' if place_label=='Select a place' else place_label
    a,b,c=st.columns(3)
    muni=a.text_input('Municipality (optional)',key=prefix+'m',value=place if district and place else '')
    ward=b.text_input('Ward (optional)',key=prefix+'w')
    area=c.text_input('Area / street (optional)',key=prefix+'a')
    result={'district':district,'place':place,'municipality':muni,'ward':ward,'area':area}
    if require_district_place and not (district and place):
        st.caption('District and place are required before submission.')
    if st.checkbox('Add coordinates',key=prefix+'coord'):
        a,b=st.columns(2);result['latitude']=a.number_input('Latitude',min_value=-90.,max_value=90.,key=prefix+'lat');result['longitude']=b.number_input('Longitude',min_value=-180.,max_value=180.,key=prefix+'lon')
    return result

def prediction(r):
    a,b,c=st.columns(3);a.metric('Language',r['detected_language']);b.metric('Urgency',r['urgency']);c.metric('Departments',len(r['departments']))
    st.write('**Predicted departments:** '+(', '.join(r['departments']) or 'Uncertain — official review required'))
    if r['urgency']=='Emergency':st.error(r['recommended_action'])
    for warning in r.get('warnings',[]):st.warning(warning)
    st.caption(r['score_type']);st.write('Normalized civic text:',r['normalized_text'])
    with st.expander('Scores, evidence and safety rules'):
        st.json({'department_scores':r['department_scores'],'urgency_scores':r['urgency_scores'],'rules':r['safety_rules'],'evidence':r['explanations']})

def receipt(r):
    st.success('Complaint stored. Save the ID and private tracking token; the token is shown only at submission.')
    st.code('ID: '+r['id']+'\nTracking token: '+r['tracking_token'],language=None)
    st.session_state['last_id']=r['id'];st.session_state['last_tracking']=r['tracking_token'];prediction(r)

def lookup(key):
    ident=st.text_input('Complaint ID',value=st.session_state.get('last_id',''),key=key+'id')
    secret=st.text_input('Private tracking token (not needed for officials)',type='password',value=st.session_state.get('last_tracking',''),key=key+'secret')
    if st.button('Load complaint',key=key+'load'):
        r=call('GET','/api/v1/grievances/'+ident,tracking=secret)
        if r:st.session_state[key]=r
    return st.session_state.get(key)

if view==views[0]:
    st.subheader(view)
    with st.expander('Supported languages and writing tips'):
        st.write('English · हिन्दी · தமிழ் · Hinglish · Tanglish. Describe the problem, exact area and whether anyone is in immediate danger. Avoid unnecessary names or phone numbers.')
        st.caption('Predictions can be wrong. Officials review uncertain routing and emergency flags.')
    text=st.text_area('Describe the issue',height=150,placeholder='English, हिन्दी, தமிழ், Hinglish or Tanglish',max_chars=5000)
    loc=location('citizen',require_district_place=True)
    consent=st.checkbox('Email me status updates (optional)');email=st.text_input('Email address') if consent else None
    if st.button('Submit grievance',type='primary'):
        if not text.strip():st.warning('Describe the issue before submitting.')
        elif not (loc.get('district') and loc.get('place')):st.warning('Select both a Tamil Nadu district and a place before submitting.')
        else:
            r=call('POST','/api/v1/grievances',json={'text':text,'location':loc,'email':email,'email_opt_in':consent})
            if r:receipt(r)
elif view==views[1]:
    st.subheader('Speak in the language you are comfortable with')
    st.markdown('<div class="cl-voice-shell"><div class="cl-section-label">VOICE IN · REVIEW · SUBMIT</div><p style="color:#785b4b;margin-bottom:0">Choose a language to guide recognition. CivicLens transcribes speech in its original language; it does not intentionally translate your words into English.</p><div class="cl-wave" aria-label="Decorative audio waveform">'+''.join('<span></span>' for _ in range(45))+'</div></div>',unsafe_allow_html=True)
    st.caption('WAV or MP3 · up to 10 MiB / 120 seconds · audio is deleted after processing. Local speech models must be installed.')
    lang_label=st.selectbox('Speech language', ['Auto-detect','Tamil · தமிழ்','Hindi · हिन्दी','English'],help='If automatic detection struggles, choose the language you are speaking. For Tamil and Hindi, use the matching language hint.')
    asr_language={'Auto-detect':'','Tamil · தமிழ்':'Tamil','Hindi · हिन्दी':'Hindi','English':'English'}[lang_label]
    audio_source=st.radio('Audio source',['Upload recording','Record microphone'],horizontal=True)
    f=st.file_uploader('Choose a voice recording',type=['wav','mp3'],help='For best results, record one speaker in a quiet place and speak naturally.') if audio_source=='Upload recording' else st.audio_input('Record your grievance')
    if f:st.audio(f)
    if f and st.button('✦ Transcribe and review',type='primary'):
        with st.spinner('Listening carefully… detecting speech and preparing your transcript'):
            r=call('POST','/api/v1/grievances/analyze-audio',files={'file':(f.name,f.getvalue(),f.type)},data={'language':asr_language})
        if r:
            st.session_state['transcript']=r['transcript'];st.session_state['voice_preview']=r['prediction'];st.session_state['asr_detected_language']=r.get('asr_language');st.session_state['asr_selected_language']=r.get('selected_language')
            st.success('Transcript ready — please review every detail before submitting.')
            st.caption(f"Selected: {r.get('selected_language','Auto-detect')} · Detected by model: {r.get('asr_language') or 'Not reported'}")
    if 'transcript' in st.session_state:
        st.markdown('<div class="cl-section-label">YOUR TRANSCRIPT · EDITABLE</div>',unsafe_allow_html=True)
        st.caption('This preview has not been stored as a complaint. Correct names, locations and details before submission.')
        corrected=st.text_area('Review and correct transcript',key='transcript',max_chars=5000,height=160)
        if st.session_state.get('voice_preview'):prediction(st.session_state['voice_preview'])
        loc=location('voice',require_district_place=True)
        if st.button('Submit corrected transcript',type='primary'):
            if not corrected.strip():st.warning('Please add or correct the complaint text before submitting.')
            elif not (loc.get('district') and loc.get('place')):st.warning('Select both a Tamil Nadu district and a place before submitting.')
            else:
                r=call('POST','/api/v1/grievances',json={'text':corrected,'source':'voice','location':loc})
                if r:
                    receipt(r)
                    st.session_state.pop('transcript',None);st.session_state.pop('voice_preview',None)
elif view==views[2]:
    st.subheader(view);r=lookup('track')
    if r:
        st.metric('Current status',r['status']);st.write('Assigned department:',r['assigned_department'] or 'Awaiting review');st.write('Resolution:',r['resolution'] or 'Not yet resolved')
        locdata=r.get('location',{});st.write('Location:',', '.join(x for x in [locdata.get('district'),locdata.get('place'),locdata.get('municipality'),locdata.get('ward'),locdata.get('area')] if x) or 'Not provided')
        if r.get('is_unsolvable'):st.warning('An official marked this complaint unsolvable: '+(r.get('unsolvable_reason') or 'Reason not provided.'))
        st.dataframe(pd.DataFrame(r['notifications']),hide_index=True);prediction(r)
elif view in (views[3],views[4]):
    st.subheader(view)
    if not token:st.info('Enter your official token in the sidebar.');st.stop()
    a,b,c=st.columns(3);department=a.selectbox('Department',['All']+DEPARTMENTS);status=b.selectbox('Status',['All','Submitted','Assigned','In Progress','Resolved','Reopened','Rejected']);urgency=c.selectbox('Urgency',['Emergency'] if view==views[4] else ['All','Routine','Urgent','Emergency'])
    q=st.text_input('Search complaint text or ID');page=st.number_input('Page',min_value=1,step=1)
    params={'offset':(page-1)*25,'limit':25,'q':q}
    for name,val in [('department',department),('status',status),('urgency',urgency)]:
        if val!='All':params[name]=val
    r=call('GET','/api/v1/grievances',params=params)
    if r:
        st.caption(f"{r['count']} matching records · 25 per page")
        if r['items']:
            st.dataframe(pd.DataFrame([{k:x[k] for k in ['id','timestamp','original_text','location','departments','urgency','status','assigned_department','is_unsolvable','unsolvable_reason','review_required']} for x in r['items']]),hide_index=True)
            st.info('Use Human feedback and reassignment to assign, start, resolve or correct a selected complaint.')
        else:st.info('No matching grievances.')
elif view==views[5]:
    st.subheader(view)
    if not token:st.info('Official authorization required.');st.stop()
    ident=st.text_input('Complaint ID for duplicate review')
    if st.button('Find possible duplicates'):
        r=call('GET',f'/api/v1/grievances/{ident}/duplicates')
        if r:st.session_state['duplicate_results']=r
    r=st.session_state.get('duplicate_results')
    if r:
        st.caption(r['mode']+' · '+r['candidate_window'])
        st.caption(f"Retrieval: {r.get('inference_ms',0):.1f} ms · threshold: {r['threshold']:.2f}. Similarity is not a duplicate probability.")
        if r['warning']:st.warning(r['warning'])
        st.dataframe(pd.DataFrame(r['items']),hide_index=True)
        st.json({'confirmed_links':r['confirmed']})
    other=st.text_input('Other complaint ID');note=st.text_input('Reason for confirmation')
    if st.button('Confirm duplicate link — preserve both originals'):
        r=call('POST',f'/api/v1/grievances/{ident}/duplicates',json={'other_id':other,'note':note})
        if r:st.success('Complaints linked; neither record was deleted.')
elif view==views[6]:
    st.subheader(view)
    if not token:st.info('Official authorization required.');st.stop()
    r=call('GET','/api/v1/analytics')
    if r:
        a,b=st.columns(2);a.metric('Stored complaints',r['total']);b.metric('Flagged at submission',r['review_required'])
        if not r['total']:st.info('Submit complaints to populate these charts.')
        st.markdown('<div class="cl-section-label">LIVE SERVICE OVERVIEW</div>',unsafe_allow_html=True)
        chart_cols=st.columns(2)
        for i,key in enumerate(['departments','urgency','status','languages']):
            with chart_cols[i%2]:
                st.markdown(f'<div style="padding:12px 0 2px;font-weight:800;color:#733c27"><span class="cl-live-dot"></span>{key.title()} <span style="color:#c4663d">↗</span></div>',unsafe_allow_html=True)
                if r[key]:
                    series=pd.Series(r[key],name='Complaints').sort_values(ascending=False)
                    maximum=max(series.values) or 1
                    rows=[]
                    for label,value in series.head(7).items():
                        safe_label=html.escape(str(label))
                        width=max(2,round(float(value)/maximum*100,1))
                        rows.append(f'<div class="cl-chart-row" style="animation-delay:{len(rows)*75}ms"><span class="cl-chart-label" title="{safe_label}">{safe_label}</span><div class="cl-chart-track"><div class="cl-chart-fill" style="--bar-width:{width}%;animation-delay:{len(rows)*90}ms"></div></div><span class="cl-chart-value">{int(value)}</span></div>')
                    st.markdown('<div class="cl-chart-card">'+''.join(rows)+'</div>',unsafe_allow_html=True)
                    with st.expander('Explore interactive chart'):
                        st.bar_chart(series,color='#e87552',horizontal=True)
                else:st.caption('No data yet — submit a few synthetic demonstration complaints to populate this chart.')
        st.markdown('<div class="cl-section-label">COMPLAINT SOLVABILITY</div>',unsafe_allow_html=True)
        solvability=r.get('solvability',{'solvable':r['total'],'unsolvable':0})
        solv_cols=st.columns(2)
        solv_cols[0].metric('Solvable',int(solvability.get('solvable',0)))
        solv_cols[1].metric('Unsolvable',int(solvability.get('unsolvable',0)))
        maximum=max([int(solvability.get('solvable',0)),int(solvability.get('unsolvable',0)),1])
        rows=[]
        for idx,(label,value) in enumerate([('Solvable',int(solvability.get('solvable',0))),('Unsolvable',int(solvability.get('unsolvable',0))) ]):
            width=max(2,round(value/maximum*100,1))
            rows.append(f'<div class="cl-chart-row" style="animation-delay:{idx*75}ms"><span class="cl-chart-label">{label}</span><div class="cl-chart-track"><div class="cl-chart-fill" style="--bar-width:{width}%;animation-delay:{idx*120}ms"></div></div><span class="cl-chart-value">{value}</span></div>')
        st.markdown('<div class="cl-chart-card">'+''.join(rows)+'</div>',unsafe_allow_html=True)
        with st.expander('Explore solvability chart'):
            st.bar_chart(pd.Series(solvability,name='Complaints'),color='#e87552')
elif view==views[7]:
    st.subheader(view);r=lookup('explain')
    if r:prediction(r['original_prediction']);st.caption('Evidence describes the original model prediction; official corrections are separate.');st.json({'current_departments':r['departments'],'current_urgency':r['urgency']})
elif view==views[8]:
    st.subheader(view)
    if not token:st.info('Official authorization required.');st.stop()
    r=lookup('feedback')
    if r:
        st.write('Current status:',r['status']);st.json(r.get('audit',[]))
        st.markdown('### Solvability decision')
        if r.get('is_unsolvable'):
            st.warning('Marked unsolvable: '+(r.get('unsolvable_reason') or 'No reason recorded'))
            st.caption('Recorded by '+str(r.get('unsolvable_by') or 'official')+' at '+str(r.get('unsolvable_at') or 'unknown time')+'. This flag is separate from lifecycle status.')
        reason=st.text_area('Reason for marking unsolvable (required)',key='unsolvable_reason_'+r['id'],max_chars=3000,placeholder='Explain why this complaint cannot be resolved by the responsible service.')
        if st.button('Mark complaint Unsolvable',key='mark_unsolvable_'+r['id']):
            if len(reason.strip())<5:st.warning('Enter a meaningful reason of at least 5 characters.')
            else:
                result=call('POST','/api/v1/grievances/'+r['id']+'/unsolvable',json={'expected_version':r['version'],'reason':reason})
                if result:st.session_state['feedback']=result;st.success('Unsolvable decision saved and audited. Lifecycle status was preserved.');st.rerun()
        ds=st.multiselect('Correct departments',DEPARTMENTS,default=r['departments'])
        urgency=st.selectbox('Correct urgency',['Routine','Urgent','Emergency'],index=['Routine','Urgent','Emergency'].index(r['urgency']))
        assigned=st.selectbox('Assign department',['No change']+DEPARTMENTS)
        status=st.selectbox('Next status',['No change','Assigned','In Progress','Resolved','Reopened','Rejected'])
        resolution=st.text_area('Resolution details');note=st.text_area('Required audit note')
        edit_location=st.checkbox('Correct location');loc=location('edit') if edit_location else None
        if st.button('Save official review',type='primary'):
            payload={'expected_version':r['version'],'urgency':urgency,'note':note}
            if ds:payload['departments']=ds
            if assigned!='No change':payload['assigned_department']=assigned
            if status!='No change':payload['status']=status
            if resolution:payload['resolution']=resolution
            if loc:payload['location']=loc
            updated=call('PATCH','/api/v1/grievances/'+r['id'],json=payload)
            if updated:st.session_state['feedback']=updated;st.success('Saved with an audit event. Reload to view the full history.')
    if st.button('Prepare private feedback export'):
        data=call('GET','/api/v1/feedback/export')
        if data:st.download_button('Download feedback JSON (sensitive)',json.dumps(data,ensure_ascii=False,indent=2),file_name='feedback.json',mime='application/json')
elif view==views[9]:
    st.subheader(view);r=call('GET','/health')
    if r:st.json(r)
    st.info('The baseline includes clearly labeled synthetic training data. Scores are uncalibrated; evaluation is a small inherited demonstration hold-out. No real municipal integration or emergency dispatch is provided.')
    if token:
        r=call('GET','/api/v1/system')
        if r:st.json(r)
