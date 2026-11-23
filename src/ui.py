"""Identidad visual de EnergyWatch AI: estilos, tarjeta de resultado y gráficos.

Paleta de tinta oscura con un acento cobre; los estados usan verde salvia, ocre y rojo arcilla.
"""

from html import escape
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

INK = '#0D1013'
SURFACE = '#151A1F'
LINE = '#262D34'
TEXT = '#E9E5DC'
MUTED = '#8C959D'
ACCENT = '#D98C4A'
STATE = {'normal': '#7FB8A4', 'atencion': '#E3C65B', 'alto': '#E0594B'}
CLUSTER_COLORS = ['#7FB8A4', '#6C8FD1', '#B68BD1', '#D1B56C']

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'IBM Plex Sans', sans-serif; }}
.stApp {{ background: {INK}; color: {TEXT}; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ max-width: 1080px; padding: 4rem 1.4rem 4rem; }}
h1, h2, h3, h4 {{ font-family: 'IBM Plex Sans', sans-serif; letter-spacing: -0.01em; color: {TEXT}; }}
[data-testid="stTabs"] [role="tablist"] {{ gap: 1.4rem; border-bottom: 1px solid {LINE}; }}
[data-testid="stTabs"] button[role="tab"] {{ padding: .6rem 0; color: {MUTED}; font-weight: 500; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ color: {TEXT}; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background: {ACCENT}; height: 2px; }}
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  border-radius: 3px; border: 1px solid {LINE}; background: {SURFACE}; color: {TEXT}; font-weight: 500; }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
  background: {ACCENT}; border-color: {ACCENT}; color: {INK}; }}
[data-testid="stMetric"] {{ background: {SURFACE}; border: 1px solid {LINE}; padding: .9rem 1rem; border-radius: 4px; }}
[data-testid="stMetricLabel"] {{ color: {MUTED}; }}
[data-testid="stMetricValue"] {{ font-family: 'IBM Plex Mono', monospace; font-weight: 500; }}
[data-testid="stExpander"] {{ border: 1px solid {LINE}; border-radius: 4px; background: {SURFACE}; }}
.ew-brand {{ font-family: 'IBM Plex Mono', monospace; letter-spacing: .22em; font-size: .78rem; color: {ACCENT}; }}
.ew-title {{ font-size: 2.1rem; font-weight: 600; margin: .15rem 0 .2rem; line-height: 1.15; }}
.ew-sub {{ color: {MUTED}; margin-bottom: 1.4rem; max-width: 640px; }}
.ew-kicker {{ font-family: 'IBM Plex Mono', monospace; font-size: .72rem; letter-spacing: .14em; color: {MUTED}; text-transform: uppercase; }}
.ew-card {{ background: {SURFACE}; border: 1px solid {LINE}; border-left: 4px solid var(--st); border-radius: 4px;
  padding: 1.3rem 1.5rem 1.2rem; margin: 1rem 0; }}
.ew-row {{ display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: .6rem; }}
.ew-big {{ font-family: 'IBM Plex Mono', monospace; font-size: 3.2rem; font-weight: 500; line-height: 1.1; }}
.ew-big span {{ font-size: 1.2rem; color: {MUTED}; margin-left: .35rem; }}
.ew-badge {{ font-family: 'IBM Plex Mono', monospace; font-size: .8rem; letter-spacing: .14em; padding: .25rem .65rem;
  border: 1px solid var(--st); color: var(--st); border-radius: 2px; text-transform: uppercase; }}
.ew-msg {{ margin: .5rem 0 1.1rem; color: {TEXT}; }}
.ew-track {{ position: relative; height: 10px; background: {INK}; border: 1px solid {LINE}; border-radius: 2px; }}
.ew-band {{ position: absolute; top: 0; bottom: 0; background: rgba(127,184,164,.28); }}
.ew-mark {{ position: absolute; top: -6px; width: 3px; height: 22px; background: var(--st); }}
.ew-scale {{ position: relative; height: 1.2rem; margin-top: .35rem; font-family: 'IBM Plex Mono', monospace; font-size: .7rem; color: {MUTED}; }}
.ew-scale span {{ position: absolute; transform: translateX(-50%); white-space: nowrap; }}
.ew-stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1.1rem; padding-top: 1rem; border-top: 1px solid {LINE}; }}
.ew-stat b {{ display: block; font-family: 'IBM Plex Mono', monospace; font-size: 1.2rem; font-weight: 500; }}
.ew-stat small {{ color: {MUTED}; }}
.ew-step {{ border-top: 2px solid {ACCENT}; padding-top: .7rem; }}
.ew-step .n {{ font-family: 'IBM Plex Mono', monospace; color: {ACCENT}; font-size: .8rem; }}
.ew-step h4 {{ margin: .15rem 0 .3rem; }}
.ew-step p {{ color: {MUTED}; font-size: .93rem; }}
@media (max-width: 640px) {{
  .ew-big {{ font-size: 2.4rem; }} .ew-title {{ font-size: 1.6rem; }} .ew-stats {{ grid-template-columns: 1fr; gap: .6rem; }}
  .block-container {{ padding: 1.2rem .9rem 3rem; }}
}}
</style>
"""


def header():
    return (
        '<div class="ew-brand">ENERGYWATCH AI</div>'
        '<div class="ew-title">¿Es normal el consumo de tu casa?</div>'
        '<div class="ew-sub">Compara el consumo eléctrico de tu hogar con más de 68.000 mediciones reales '
        'y te dice, sin tecnicismos, si es habitual.</div>'
    )


def steps(items):
    """items: lista de (número, título, texto)."""
    return ''.join(
        f'<div class="ew-step"><span class="n">{n}</span><h4>{escape(t)}</h4><p>{escape(d)}</p></div>'
        for n, t, d in items
    )


def result_card(nivel, label, message, total_w, p05_kw, p95_kw, kwh, cost, cluster):
    """Tarjeta con el estado, el consumo dentro del rango histórico y el costo diario."""
    top = max(6.0, p95_kw * 1.6, total_w / 1000 * 1.15)
    pos = lambda kw: min(max(kw / top, 0), 1) * 100
    cost_txt = f'$ {cost:,.0f}'.replace(',', '.') if cost else 'sin precio'
    cluster_txt = 'ruido (-1)' if cluster < 0 else f'clúster {cluster}'
    return f"""
<div class="ew-card" style="--st:{STATE[nivel]}">
  <div class="ew-kicker">Resultado · promedio de 30 minutos</div>
  <div class="ew-row">
    <div class="ew-big">{total_w:,.0f}<span>W</span></div>
    <div class="ew-badge">{escape(label)}</div>
  </div>
  <div class="ew-msg">{escape(message)}</div>
  <div class="ew-track">
    <div class="ew-band" style="left:{pos(p05_kw):.1f}%; width:{pos(p95_kw) - pos(p05_kw):.1f}%"></div>
    <div class="ew-mark" style="left:{pos(total_w / 1000):.1f}%"></div>
  </div>
  <div class="ew-scale">
    <span style="left:{pos(p05_kw):.1f}%">p5 {p05_kw:.2f} kW</span>
    <span style="left:{max(pos(p95_kw), pos(p05_kw) + 22):.1f}%">p95 {p95_kw:.2f} kW</span>
  </div>
  <div class="ew-stats">
    <div class="ew-stat"><b>{kwh:.1f} kWh</b><small>si se mantiene 24 h</small></div>
    <div class="ew-stat"><b>{cost_txt}</b><small>COP por día</small></div>
    <div class="ew-stat"><b>{cluster_txt}</b><small>grupo más cercano (DBSCAN)</small></div>
  </div>
</div>
"""


def _axes(figsize=(8, 3.2)):
    fig, ax = plt.subplots(figsize=figsize, dpi=160)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(LINE)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.grid(axis='y', color=LINE, linewidth=.6)
    ax.set_axisbelow(True)
    return fig, ax


def history_chart(history, p05_kw, p95_kw):
    """Consumo de cada consulta (W) sobre la banda histórica habitual."""
    data = history.sort_values('creado')
    fig, ax = _axes()
    ax.axhspan(p05_kw * 1000, p95_kw * 1000, color=STATE['normal'], alpha=.12, lw=0)
    ax.text(data['creado'].iloc[-1], p05_kw * 1000 + 60, 'rango habitual (p5–p95) ', color=MUTED, fontsize=7, va='bottom', ha='right')
    ax.plot(data['creado'], data['Global_active_power'] * 1000, color=MUTED, lw=.9, zorder=2)
    for nivel, color in STATE.items():
        sub = data[data['nivel'] == nivel]
        ax.scatter(sub['creado'], sub['Global_active_power'] * 1000, s=22, color=color, zorder=3, label=nivel)
    ax.set_ylabel('W', color=MUTED, fontsize=8)
    fig.autofmt_xdate(rotation=0, ha='center')
    fig.tight_layout()
    return fig


def density_map(replay, point=None):
    """Ventanas reales coloreadas por grupo DBSCAN; el punto del usuario se superpone."""
    fig, ax = _axes((8, 3.8))
    noise = replay[replay['cluster'] == -1]
    for k in sorted(replay['cluster'].unique()):
        if k < 0:
            continue
        sub = replay[replay['cluster'] == k]
        ax.scatter(
            sub['Global_active_power'], sub['Sub_metering_3'], s=9, alpha=.55, lw=0,
            color=CLUSTER_COLORS[k % len(CLUSTER_COLORS)], label=f'Clúster {k}',
        )
    ax.scatter(noise['Global_active_power'], noise['Sub_metering_3'], s=22, marker='x', lw=.9, color=STATE['alto'], label='Ruido (atípico)')
    if point is not None:
        ax.scatter([point[0]], [point[1]], s=90, facecolor='none', edgecolor=ACCENT, lw=1.8, zorder=5, label='Tu consulta')
    ax.set_xlabel('Potencia activa (kW)', color=MUTED, fontsize=8)
    ax.set_ylabel('Calentador / aire (Wh por min)', color=MUTED, fontsize=8)
    leg = ax.legend(frameon=False, fontsize=7.5, labelcolor=TEXT, loc='upper right')
    for h in leg.legend_handles:
        h.set_alpha(1)
    fig.tight_layout()
    return fig


def replay_chart(subset, p05_kw, p95_kw):
    """Potencia de la reproducción histórica; marca en rojo las ventanas atípicas."""
    fig, ax = _axes((8, 2.8))
    ax.axhspan(p05_kw, p95_kw, color=STATE['normal'], alpha=.12, lw=0)
    ax.plot(subset['timestamp'], subset['Global_active_power'], color=MUTED, lw=1)
    odd = subset[subset['cluster'] == -1]
    ax.scatter(odd['timestamp'], odd['Global_active_power'], color=STATE['alto'], s=28, zorder=3)
    ax.set_ylabel('kW', color=MUTED, fontsize=8)
    ax.set_ylim(0, max(float(subset['Global_active_power'].max()) * 1.15, p95_kw * 1.2))
    fig.autofmt_xdate(rotation=0, ha='center')
    fig.tight_layout()
    return fig


def close(fig):
    plt.close(fig)
    return fig
