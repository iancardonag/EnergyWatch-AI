"""La casa en corte: dibujo SVG cuyas habitaciones se iluminan según los vatios de cada zona.

Cada habitación corresponde a una zona del catálogo y a un submedidor del dataset UCI:
cocina (Sub_metering_1), lavandería y nevera (Sub_metering_2), baño con ducha o calentador
(Sub_metering_3) y sala con el resto de aparatos.
"""

INK = '#1E1915'
PAPER = '#FBF7EE'
GLOW = '#F5C14B'
ACCENT = '#C2502A'
LEVEL_COLOR = {'normal': '#2E6B58', 'atencion': '#C98F0A', 'alto': '#B3261E'}
LEVEL_WORD = {'normal': 'HABITUAL', 'atencion': 'REVISAR', 'alto': 'ALERTA'}

# watts de cada zona a partir de los cuales la habitación se ve "a plena luz"
FULL_LIGHT_W = {'cocina': 3000, 'lavanderia': 1500, 'agua_aire': 4500, 'otros': 1500}

ROOMS = {
    # zona: (x, y, nombre)
    'agua_aire': (60, 150, 'BAÑO · DUCHA / AIRE'),
    'otros': (310, 150, 'SALA · OTROS'),
    'cocina': (60, 285, 'COCINA'),
    'lavanderia': (310, 285, 'LAVANDERÍA · NEVERA'),
}
W, H = 250, 135


def _glyphs(zone, rx, ry, on):
    """Dibujo de línea de los aparatos de cada habitación."""
    c = ACCENT if on else INK
    s = f'fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    if zone == 'agua_aire':
        return f"""
<g {s}>
  <path d="M{rx+168} {ry+18} v14 h-22 M{rx+146} {ry+32} a26 12 0 0 0 52 0 Z"/>
  <path class="drip" d="M{rx+152} {ry+58} v14 M{rx+163} {ry+62} v18 M{rx+174} {ry+58} v14 M{rx+185} {ry+62} v18" stroke-dasharray="5 6"/>
  <path d="M{rx+130} {ry+112} h100 M{rx+140} {ry+112} v-8 h80 v8"/>
  <rect x="{rx+24}" y="{ry+22}" width="64" height="22" rx="3"/>
  <path d="M{rx+32} {ry+34} h48 M{rx+32} {ry+39} h48"/>
</g>"""
    if zone == 'otros':
        return f"""
<g {s}>
  <rect x="{rx+34}" y="{ry+46}" width="76" height="46" rx="3"/>
  <path d="M{rx+72} {ry+92} v12 M{rx+52} {ry+104} h40"/>
  <path d="M{rx+138} {ry+86} q0 -14 14 -14 h66 q14 0 14 14 v26 h-94 Z M{rx+138} {ry+86} q-10 0 -10 10 v16"/>
  <path d="M{rx+228} {ry+60} v52 M{rx+218} {ry+52} h20 l-4 -14 h-12 Z"/>
</g>"""
    if zone == 'cocina':
        return f"""
<g {s}>
  <path d="M{rx+30} {ry+34} l12 -14 h52 l12 14 Z"/>
  <rect x="{rx+30}" y="{ry+58}" width="80" height="54" rx="2"/>
  <rect x="{rx+40}" y="{ry+78}" width="60" height="26" rx="2"/>
  <circle cx="{rx+48}" cy="{ry+68}" r="4"/><circle cx="{rx+68}" cy="{ry+68}" r="4"/><circle cx="{rx+88}" cy="{ry+68}" r="4"/>
  <path d="M{rx+126} {ry+112} h104 M{rx+140} {ry+112} v-24 h80 v24"/>
  <rect x="{rx+150}" y="{ry+68}" width="34" height="20" rx="3"/>
  <circle cx="{rx+200}" cy="{ry+76}" r="9"/>
</g>"""
    return f"""
<g {s}>
  <rect x="{rx+24}" y="{ry+52}" width="62" height="60" rx="3"/>
  <circle cx="{rx+55}" cy="{ry+86}" r="18"/><circle cx="{rx+55}" cy="{ry+86}" r="9"/>
  <path d="M{rx+32} {ry+62} h10 M{rx+66} {ry+62} h12"/>
  <rect x="{rx+160}" y="{ry+22}" width="50" height="90" rx="4"/>
  <path d="M{rx+160} {ry+58} h50 M{rx+168} {ry+36} v12 M{rx+168} {ry+68} v18"/>
</g>"""


def _room(zone, watts):
    rx, ry, label = ROOMS[zone]
    full = FULL_LIGHT_W[zone]
    level = max(0.0, min(watts / full, 1.0))
    on = watts > 0
    glow = f"""
<g clip-path="url(#clip-{zone})">
  <rect x="{rx}" y="{ry}" width="{W}" height="{H}" fill="{GLOW}" opacity="{0.12 + 0.38 * level:.2f}"/>
  <circle cx="{rx + W / 2}" cy="{ry + 14}" r="{90 + 90 * level:.0f}" fill="url(#glow)" opacity="{0.25 + 0.75 * level:.2f}"/>
</g>""" if on else ''
    lamp = f'<path d="M{rx + W / 2} {ry} v12" stroke="{INK}" stroke-width="2"/><circle cx="{rx + W / 2}" cy="{ry + 16}" r="5" fill="{GLOW if on else PAPER}" stroke="{INK}" stroke-width="2"/>'
    tag = f'<text x="{rx + 10}" y="{ry + H - 7}" class="hs-lab">{label}</text>'
    num = f'<text x="{rx + W - 10}" y="{ry + H - 6}" text-anchor="end" class="hs-num" fill="{ACCENT if on else "#9A8E80"}">{watts:,.0f} W</text>'.replace(',', '.')
    return glow + lamp + _glyphs(zone, rx, ry, on) + tag + num


def _meter(total_w):
    digits = f'{min(int(round(total_w)), 99999):05d}'
    cells = ''.join(
        f'<rect x="{608 + i * 12}" y="318" width="11" height="17" fill="{INK}"/>'
        f'<text x="{613.5 + i * 12}" y="331" text-anchor="middle" class="hs-dig">{d}</text>'
        for i, d in enumerate(digits)
    )
    return f"""
<g>
  <path d="M570 262 H590 M590 262 V250" stroke="{INK}" stroke-width="2" fill="none"/>
  <rect x="592" y="238" width="86" height="116" rx="10" fill="{PAPER}" stroke="{INK}" stroke-width="2.5"/>
  <circle cx="635" cy="282" r="30" fill="#fff" stroke="{INK}" stroke-width="2"/>
  <circle cx="635" cy="282" r="19" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-dasharray="3 4"/>
  <path class="spin" d="M635 282 L635 262" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>
  <circle cx="635" cy="282" r="3" fill="{INK}"/>
  {cells}
  <text x="635" y="349" text-anchor="middle" class="hs-lab">W · 30 MIN</text>
</g>"""


def _stamp(nivel):
    if nivel not in LEVEL_WORD:
        return ''
    col = LEVEL_COLOR[nivel]
    word = LEVEL_WORD[nivel]
    w = 30 + 21 * len(word)
    return f"""
<g transform="translate(86 96) rotate(-7)">
  <rect x="0" y="0" width="{w}" height="46" rx="3" fill="{PAPER}" fill-opacity=".9" stroke="{col}" stroke-width="4"/>
  <rect x="5" y="5" width="{w - 10}" height="36" rx="1" fill="none" stroke="{col}" stroke-width="1.2"/>
  <text x="{w / 2}" y="33" text-anchor="middle" class="hs-stamp" fill="{col}">{word}</text>
</g>"""


def house_svg(zones, total_w=None, nivel=None):
    """SVG de la casa. `zones` = {'cocina','lavanderia','agua_aire','otros'} en vatios."""
    zones = {z: float(zones.get(z, 0.0)) for z in ROOMS}
    total = sum(zones.values()) if total_w is None else total_w
    defs = f"""
<defs>
  <radialGradient id="glow"><stop offset="0" stop-color="{GLOW}" stop-opacity=".95"/><stop offset="1" stop-color="{GLOW}" stop-opacity="0"/></radialGradient>
  {''.join(f'<clipPath id="clip-{z}"><rect x="{x}" y="{y}" width="{W}" height="{H}"/></clipPath>' for z, (x, y, _) in ROOMS.items())}
  <pattern id="hatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0 V9" stroke="{INK}" stroke-width="1" opacity=".35"/></pattern>
  <pattern id="tiles" width="14" height="10" patternUnits="userSpaceOnUse"><path d="M0 10 Q7 0 14 10" fill="none" stroke="{INK}" stroke-width="1" opacity=".55"/></pattern>
</defs>"""
    return f"""
<svg class="house" viewBox="0 0 700 452" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Casa en corte con el consumo por habitación">
{defs}
<path d="M30 150 L310 36 L590 150 Z" fill="url(#tiles)" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>
<path d="M30 150 L310 36 L590 150" fill="none" stroke="{ACCENT}" stroke-width="3" stroke-linejoin="round" opacity=".0"/>
<rect x="420" y="52" width="26" height="62" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>
<rect x="60" y="150" width="500" height="270" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>
{''.join(_room(z, zones[z]) for z in ROOMS)}
<path d="M60 285 H560 M310 150 V420" stroke="{INK}" stroke-width="3"/>
<rect x="60" y="420" width="500" height="10" fill="url(#hatch)"/>
<path d="M20 420 H690" stroke="{INK}" stroke-width="3"/>
<rect x="20" y="420" width="670" height="24" fill="url(#hatch)" opacity=".6"/>
{_meter(total)}
{_stamp(nivel)}
</svg>"""


def zones_from_watts(total_w, cocina_w, lavanderia_w, agua_aire_w):
    """Zonas de la casa a partir de los cuatro valores del modo «Ya conozco mis vatios»."""
    other = max(total_w - cocina_w - lavanderia_w - agua_aire_w, 0.0)
    return {'cocina': cocina_w, 'lavanderia': lavanderia_w, 'agua_aire': agua_aire_w, 'otros': other}


def room_svg(zone, watts):
    """Ilustración de una sola habitación (para la tarjeta de cada cuarto)."""
    on = watts > 0
    lamp = (
        f'<path d="M125 0 v12" stroke="{INK}" stroke-width="2"/>'
        f'<circle cx="125" cy="16" r="5" fill="{GLOW if on else PAPER}" stroke="{INK}" stroke-width="2"/>'
    )
    return f'<svg class="roomsvg" viewBox="0 0 250 122" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{lamp}{_glyphs(zone, 0, 0, on)}</svg>'


def roof_svg(nivel=None):
    """Techo de la casa con chimenea; recibe el sello del veredicto."""
    stamp = ''
    if nivel in LEVEL_WORD:
        col, word = LEVEL_COLOR[nivel], LEVEL_WORD[nivel]
        w = 40 + 30 * len(word)
        stamp = f"""
<g transform="translate({500 - w / 2} 72) rotate(-4 {w / 2} 30)">
  <rect width="{w}" height="62" rx="4" fill="{PAPER}" fill-opacity=".94" stroke="{col}" stroke-width="5"/>
  <rect x="7" y="7" width="{w - 14}" height="48" fill="none" stroke="{col}" stroke-width="1.5"/>
  <text x="{w / 2}" y="44" text-anchor="middle" class="hs-stamp" style="font-size:34px" fill="{col}">{word}</text>
</g>"""
    return f"""
<svg class="roof" viewBox="0 0 1000 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Techo de la casa">
<defs><pattern id="tiles2" width="16" height="11" patternUnits="userSpaceOnUse"><path d="M0 11 Q8 0 16 11" fill="none" stroke="{INK}" stroke-width="1.1" opacity=".5"/></pattern></defs>
<rect x="740" y="14" width="40" height="92" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>
<path d="M-10 148 L500 8 L1010 148 Z" fill="url(#tiles2)" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>
{stamp}
</svg>"""


def meter_svg(total_w):
    """Medidor de pared con aguja giratoria y dígitos con el total en vatios."""
    digits = f'{min(int(round(total_w)), 99999):05d}'
    cells = ''.join(
        f'<rect x="{18 + i * 23}" y="116" width="21" height="32" fill="{INK}"/>'
        f'<text x="{28.5 + i * 23}" y="140" text-anchor="middle" style="font:500 24px \'DM Mono\',monospace;fill:{PAPER}">{d}</text>'
        for i, d in enumerate(digits)
    )
    return f"""
<svg class="meter" viewBox="0 0 150 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Medidor: {total_w:.0f} vatios">
  <rect x="3" y="3" width="144" height="184" rx="14" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>
  <circle cx="75" cy="62" r="42" fill="#fff" stroke="{INK}" stroke-width="2.5"/>
  <circle cx="75" cy="62" r="28" fill="none" stroke="{ACCENT}" stroke-width="2.5" stroke-dasharray="4 5"/>
  <path d="M75 62 L75 30" stroke="{INK}" stroke-width="3.5" stroke-linecap="round">
    <animateTransform attributeName="transform" type="rotate" from="0 75 62" to="360 75 62" dur="7s" repeatCount="indefinite"/>
  </path>
  <circle cx="75" cy="62" r="4.5" fill="{INK}"/>
  {cells}
  <text x="75" y="171" text-anchor="middle" class="hs-lab" style="font-size:11px">VATIOS · 30 MIN</text>
</svg>"""
