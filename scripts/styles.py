"""Shared UI helpers and style for the Streamlit application.

Keeps the visual system (colours, spacing, typography, cards) in one place so
the demo looks polished and consistent without adding runtime dependencies.
"""

import streamlit as st


# ==============================
# Global theme (injected CSS)
# ==============================

GLOBAL_CSS = """
<style>
:root {
    --prc-bg: #0d1117;
    --prc-surface: #161b22;
    --prc-surface-2: #1f2630;
    --prc-border: #30363d;
    --prc-text: #e6edf3;
    --prc-muted: #8b949e;
    --prc-accent: #2f81f7;
    --prc-accent-soft: rgba(47,129,247,0.12);
    --prc-success: #3fb950;
    --prc-warn: #d29922;
    --prc-danger: #f85149;
}

/* App background */
.stApp {
    background:
        radial-gradient(1000px 500px at 80% -10%, rgba(47,129,247,0.08), transparent 60%),
        linear-gradient(180deg, #0d1117 0%, #0a0e14 100%);
    color: var(--prc-text);
}

/* Branding hero */
.prc-hero {
    border: 1px solid var(--prc-border);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    background:
        linear-gradient(180deg, rgba(47,129,247,0.10), rgba(47,129,247,0.02)),
        var(--prc-surface);
    box-shadow: 0 1px 0 rgba(255,255,255,0.04) inset;
}
.prc-hero h1 {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0 0 0.3rem 0;
    color: #fff;
}
.prc-hero .prc-tag {
    font-size: 1rem;
    font-weight: 600;
    color: var(--prc-accent);
    margin: 0 0 0.5rem 0;
}
.prc-hero p {
    color: var(--prc-muted);
    margin: 0;
    font-size: 0.95rem;
    line-height: 1.5;
}

/* Metric cards */
.prc-metric {
    border: 1px solid var(--prc-border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    background: linear-gradient(180deg, rgba(47,129,247,0.06), rgba(47,129,247,0.01));
    height: 100%;
}
.prc-metric .m-label {
    color: var(--prc-muted);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
}
.prc-metric .m-value {
    font-size: 1.7rem;
    font-weight: 800;
    color: #fff;
    line-height: 1.2;
    margin-top: 0.2rem;
}
.prc-metric .m-hint {
    color: var(--prc-muted);
    font-size: 0.75rem;
    margin-top: 0.35rem;
}

/* Section headings */
.prc-section {
    border-left: 3px solid var(--prc-accent);
    padding: 0.1rem 0.9rem;
    margin: 1.2rem 0 0.5rem 0;
}
.prc-section h3 {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 700;
    color: #fff;
}
.prc-section p {
    margin: 0.2rem 0 0 0;
    color: var(--prc-muted);
    font-size: 0.85rem;
}

/* Status pills */
.prc-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
}
.prc-pill.success { background: rgba(63,185,80,0.15); color: var(--prc-success); }
.prc-pill.danger  { background: rgba(248,81,73,0.15); color: var(--prc-danger); }
.prc-pill.neutral { background: rgba(139,148,158,0.15); color: var(--prc-muted); }

/* Chain row */
.prc-chain {
    display: flex; gap: 12px; flex-wrap: wrap; margin: 0.4rem 0;
}
.prc-badge {
    border: 1px solid var(--prc-border);
    background: var(--prc-surface);
    border-radius: 8px;
    padding: 0.45rem 0.8rem;
    font-size: 0.8rem;
    color: var(--prc-muted);
}
.prc-badge b { color: #fff; font-weight: 600; }

/* Keyboard / hash short display */
.prc-hash {
    font-family: "SFMono-Regular", Consolas, monospace;
    font-size: 0.82rem;
    color: var(--prc-accent);
    word-break: break-all;
}

/* Table polish */
.stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ==============================
# Reusable components
# ==============================

def hero(title, tagline, description):
    """Branding hero block shown at the top of the app."""
    st.markdown(
        f"""
        <div class="prc-hero">
            <h1>{title}</h1>
            <div class="prc-tag">{tagline}</div>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title, blurb=""):
    """Section heading with an accent border."""
    body = f"<p>{blurb}</p>" if blurb else ""
    st.markdown(
        f'<div class="prc-section"><h3>{title}</h3>{body}</div>',
        unsafe_allow_html=True,
    )


def metric_card(label, value, hint=""):
    """Render one metric card (fill a column)."""
    hint_html = f'<div class="m-hint">{hint}</div>' if hint else ""
    st.markdown(
        f"""
        <div class="prc-metric">
            <div class="m-label">{label}</div>
            <div class="m-value">{value}</div>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def short_hash(hash_str, head=10, tail=4):
    """Shorten a long hash for display: 0x25a7...5E81."""
    if hash_str is None:
        return ""
    h = hash_str
    if len(h) <= head + tail + 3:
        return h
    return f"{h[:head]}...{h[-tail:]}"


def chain_badges(items):
    """Render a row of small key/value badges (network, chain, contracts)."""
    parts = "".join(
        f'<span class="prc-badge">{key}: <b>{val}</b></span>'
        for key, val in items
    )
    st.markdown(f'<div class="prc-chain">{parts}</div>', unsafe_allow_html=True)
