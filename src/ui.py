"""Identidad visual de EnergyWatch AI: papel cálido, tinta, terracota y una casa en corte.

La interfaz imita un cuaderno técnico de arquitectura: papel milimetrado, rótulos en mono,
sellos de goma para el veredicto y la casa dibujada como protagonista.
"""

from html import escape
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

PAPER = '#F4EDDF'
CARD = '#FBF7EE'
INK = '#1E1915'
MUTED = '#7A6F63'
LINE = '#D9CDB8'
ACCENT = '#C2502A'
STATE = {'normal': '#2E6B58', 'atencion': '#C98F0A', 'alto': '#B3261E'}
CLUSTER_COLORS = ['#2E6B58', '#3E5C8A', '#8A5A83', '#B07D2B']

SVG_CSS = f"""
.house {{ width: 100%; height: auto; display: block; }}
.hs-lab {{ font: 500 9.5px 'DM Mono', monospace; letter-spacing: .08em; fill: {MUTED}; }}
.hs-num {{ font: 600 15px 'Fraunces', Georgia, serif; }}
.hs-dig {{ font: 500 12px 'DM Mono', monospace; fill: {CARD}; }}
.hs-stamp {{ font: 700 25px 'DM Mono', monospace; letter-spacing: .12em; }}
.drip {{ animation: drip 1.1s linear infinite; }}
.spin {{ transform-origin: 635px 282px; animation: spin 6s linear infinite; }}
@keyframes drip {{ to {{ stroke-dashoffset: -22; }} }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
"""

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500&family=Instrument+Sans:wght@400;500;600&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Instrument Sans', sans-serif; }}
.stApp {{ background-color: {PAPER}; color: {INK};
  background-image: linear-gradient(rgba(30,25,21,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(30,25,21,.045) 1px, transparent 1px);
  background-size: 28px 28px; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ max-width: 1120px; padding: 3.6rem 1.4rem 4rem; }}
h1, h2, h3, h4 {{ font-family: 'Fraunces', Georgia, serif; font-weight: 600; letter-spacing: -.01em; color: {INK}; }}
[data-testid="stTabs"] [role="tablist"] {{ gap: .35rem; border-bottom: 2px solid {INK}; }}
[data-testid="stTabs"] button[role="tab"] {{ padding: .55rem 1.1rem !important; color: {MUTED}; font-weight: 500; border: 1.5px solid transparent;
  border-bottom: none; border-radius: 8px 8px 0 0; margin-bottom: -2px; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ color: {INK}; background: {CARD}; border-color: {INK}; border-bottom: 2px solid {CARD}; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"], [data-testid="stTabs"] [data-baseweb="tab-border"] {{ display: none; }}
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  border-radius: 3px; border: 1.5px solid {INK}; background: {CARD}; color: {INK}; font-weight: 600; box-shadow: 3px 3px 0 {LINE}; }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
  background: {ACCENT}; border-color: {INK}; color: #fff; box-shadow: 3px 3px 0 {INK}; }}
[data-testid="stMetric"] {{ background: {CARD}; border: 1.5px solid {INK}; padding: .9rem 1rem; border-radius: 3px; box-shadow: 4px 4px 0 {LINE}; }}
[data-testid="stMetricLabel"] {{ color: {MUTED}; }}
[data-testid="stMetricValue"] {{ font-family: 'Fraunces', serif; font-weight: 600; }}
[data-testid="stExpander"] {{ border: 1.5px solid {INK}; border-radius: 3px; background: {CARD}; }}
.ew-brand {{ font-family: 'DM Mono', monospace; letter-spacing: .22em; font-size: .78rem; color: {ACCENT}; }}
.ew-title {{ font-family: 'Fraunces', serif; font-size: 2.9rem; font-weight: 600; margin: .1rem 0 .3rem; line-height: 1.05; letter-spacing: -.02em; }}
.ew-title em {{ color: {ACCENT}; font-weight: 500; }}
.ew-sub {{ color: {MUTED}; margin-bottom: 1.4rem; max-width: 620px; font-size: 1.05rem; }}
.ew-kicker {{ font-family: 'DM Mono', monospace; font-size: .72rem; letter-spacing: .14em; color: {MUTED}; text-transform: uppercase; }}
[data-testid="stColumn"]:has(.ew-plate) {{ position: sticky; top: 3.4rem; align-self: flex-start; }}
.ew-plate {{ background: {CARD}; border: 1.5px solid {INK}; border-radius: 3px; box-shadow: 5px 5px 0 {LINE}; padding: 1rem 1.1rem .6rem; }}
.ew-card {{ background: {CARD}; border: 1.5px solid {INK}; border-radius: 3px; box-shadow: 5px 5px 0 var(--st); padding: 1.3rem 1.5rem 1.2rem; margin: 1rem 0 1.4rem; }}
.ew-row {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: .6rem; }}
.ew-big {{ font-family: 'Fraunces', serif; font-size: 3.6rem; font-weight: 600; line-height: 1.05; letter-spacing: -.02em; }}
.ew-big span {{ font-family: 'DM Mono', monospace; font-size: 1.1rem; color: {MUTED}; margin-left: .35rem; letter-spacing: 0; }}
.ew-badge {{ font-family: 'DM Mono', monospace; font-weight: 500; font-size: 1rem; letter-spacing: .16em; padding: .3rem .8rem; border: 3px double var(--st);
  color: var(--st); border-radius: 3px; text-transform: uppercase; transform: rotate(-4deg); }}
.ew-msg {{ margin: .6rem 0 1.2rem; font-size: 1.05rem; }}
.ew-track {{ position: relative; height: 16px; border-bottom: 2px solid {INK};
  background: repeating-linear-gradient(90deg, {INK} 0 1px, transparent 1px 12px) bottom/100% 7px no-repeat; }}
.ew-band {{ position: absolute; top: 0; bottom: 0; background: rgba(46,107,88,.22); border-left: 2px solid {STATE['normal']}; border-right: 2px solid {STATE['normal']}; }}
.ew-mark {{ position: absolute; top: -8px; width: 0; height: 0; margin-left: -8px; border-left: 8px solid transparent; border-right: 8px solid transparent;
  border-top: 14px solid var(--st); }}
.ew-scale {{ position: relative; height: 1.3rem; margin-top: .4rem; font-family: 'DM Mono', monospace; font-size: .7rem; color: {MUTED}; }}
.ew-scale span {{ position: absolute; transform: translateX(-50%); white-space: nowrap; }}
.ew-stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1.1rem; padding-top: 1rem; border-top: 1.5px dashed {LINE}; }}
.ew-stat b {{ display: block; font-family: 'Fraunces', serif; font-size: 1.5rem; font-weight: 600; }}
.ew-stat small {{ color: {MUTED}; }}
.ew-step {{ border-top: 2px solid {INK}; padding-top: .7rem; }}
.ew-step .n {{ font-family: 'Fraunces', serif; font-style: italic; color: {ACCENT}; font-size: 1.5rem; }}
.ew-step h4 {{ margin: .1rem 0 .3rem; }}
.ew-step p {{ color: {MUTED}; font-size: .95rem; }}
{SVG_CSS}
@media (max-width: 640px) {{
  .ew-big {{ font-size: 2.6rem; }} .ew-title {{ font-size: 2rem; }} .ew-stats {{ grid-template-columns: 1fr; gap: .6rem; }}
  .block-container {{ padding: 1.4rem .9rem 3rem; }}
}}
</style>
"""


def header():
    return (
        '<div class="ew-brand">ENERGYWATCH AI · CUADERNO DE CONSUMO</div>'
        '<div class="ew-title">¿Es <em>normal</em> el consumo<br>de tu casa?</div>'
        '<div class="ew-sub">Prende los aparatos en cada habitación y mira cómo se ilumina la casa. '
        'Comparamos tu consumo con más de 68.000 mediciones reales.</div>'
    )


def plate(svg, caption=''):
    """Marco tipo lámina de plano alrededor de la casa."""
    cap = f'<div class="ew-kicker" style="margin:.2rem 0 .5rem">{escape(caption)}</div>' if caption else ''
    return f'<div class="ew-plate">{svg}{cap}</div>'


def steps(items):
    """items: lista de (número, título, texto)."""
    return ''.join(
        f'<div class="ew-step"><span class="n">{n}</span><h4>{escape(t)}</h4><p>{escape(d)}</p></div>'
        for n, t, d in items
    )


def result_card(nivel, label, message, total_w, p05_kw, p95_kw, kwh, cost, cluster):
    """Tarjeta con el estado, el consumo sobre una regla con el rango habitual y el costo diario."""
    top = max(6.0, p95_kw * 1.6, total_w / 1000 * 1.15)
    pos = lambda kw: min(max(kw / top, 0), 1) * 100
    cost_txt = f'$ {cost:,.0f}'.replace(',', '.') if cost else 'sin precio'
    cluster_txt = 'ruido (−1)' if cluster < 0 else f'clúster {cluster}'
    return f"""
<div class="ew-card" style="--st:{STATE[nivel]}">
  <div class="ew-kicker">Lectura del medidor · promedio de 30 minutos</div>
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
    <span style="left:{max(pos(p95_kw), pos(p05_kw) + 22):.1f}%">p95 {p95_kw:.2f} kW · rango habitual</span>
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
    fig.patch.set_facecolor(CARD)
    ax.set_facecolor(CARD)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(INK)
        ax.spines[side].set_linewidth(1.2)
    ax.tick_params(colors=MUTED, labelsize=8, length=3)
    ax.grid(color=LINE, linewidth=.6, linestyle=(0, (4, 4)))
    ax.set_axisbelow(True)
    return fig, ax


def history_chart(history, p05_kw, p95_kw):
    """Cada consulta como un trazo vertical desde cero, sobre la banda del rango habitual."""
    data = history.sort_values('creado')
    fig, ax = _axes()
    ax.axhspan(p05_kw * 1000, p95_kw * 1000, color=STATE['normal'], alpha=.13, lw=0)
    ax.text(data['creado'].iloc[-1], p95_kw * 1000 + 90, 'rango habitual (p5–p95)', color=STATE['normal'], fontsize=7.5, va='bottom', ha='right',
            bbox=dict(facecolor=CARD, edgecolor='none', pad=1.5, alpha=.9), zorder=6)
    for nivel, color in STATE.items():
        sub = data[data['nivel'] == nivel]
        ax.vlines(sub['creado'], 0, sub['Global_active_power'] * 1000, color=color, lw=2.2, zorder=3)
        ax.scatter(sub['creado'], sub['Global_active_power'] * 1000, s=26, color=color, edgecolor=CARD, lw=1, zorder=4)
    ax.set_ylabel('vatios', color=MUTED, fontsize=8)
    ax.set_ylim(bottom=0)
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
            sub['Global_active_power'], sub['Sub_metering_3'], s=11, alpha=.5, lw=0,
            color=CLUSTER_COLORS[k % len(CLUSTER_COLORS)], label=f'Clúster {k}',
        )
    ax.scatter(noise['Global_active_power'], noise['Sub_metering_3'], s=26, marker='x', lw=1.1, color=ACCENT, label='Ruido (atípico)')
    if point is not None:
        ax.scatter([point[0]], [point[1]], s=130, facecolor='none', edgecolor=INK, lw=2, zorder=5, label='Tu consulta')
    ax.set_xlabel('Potencia activa (kW)', color=MUTED, fontsize=8)
    ax.set_ylabel('Calentador / aire (Wh por min)', color=MUTED, fontsize=8)
    leg = ax.legend(frameon=False, fontsize=7.5, labelcolor=INK, loc='upper right')
    for h in leg.legend_handles:
        h.set_alpha(1)
    fig.tight_layout()
    return fig


def replay_chart(subset, p05_kw, p95_kw):
    """Potencia de la reproducción histórica; marca en terracota las ventanas atípicas."""
    fig, ax = _axes((8, 2.8))
    ax.axhspan(p05_kw, p95_kw, color=STATE['normal'], alpha=.13, lw=0)
    ax.plot(subset['timestamp'], subset['Global_active_power'], color=INK, lw=1.2)
    odd = subset[subset['cluster'] == -1]
    ax.scatter(odd['timestamp'], odd['Global_active_power'], color=ACCENT, s=34, zorder=3)
    ax.set_ylabel('kW', color=MUTED, fontsize=8)
    ax.set_ylim(0, max(float(subset['Global_active_power'].max()) * 1.15, p95_kw * 1.2))
    fig.autofmt_xdate(rotation=0, ha='center')
    fig.tight_layout()
    return fig


def close(fig):
    plt.close(fig)
    return fig
