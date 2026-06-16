"""Deep Agent Storm Swarm — Chat-first ANSI TUI.

Catppuccin Mocha · curses · no external dependencies
Works on Termux/Android, Linux, macOS.

Run with:
    python -m high_agent_engine tui
"""

import curses
import sys
import time
import textwrap
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .engine import RegimeEngine
from .regime import Regime
from .filesystem import FileTree, color_line


# ── Catppuccin Mocha 256-color palette ────────────────────────────────────────

_MOCHA = {
    "base":    236,
    "surface": 237,
    "overlay": 238,
    "subtext": 245,
    "text":    253,
    "mauve":   183,
    "blue":    111,
    "green":   150,
    "teal":    115,
    "yellow":  222,
    "peach":   216,
    "red":     210,
    "pink":    219,
    "lavender":147,
}

# 8-color fallback mapping (name → curses color constant)
_FALLBACK_8 = {
    "mauve":   curses.COLOR_MAGENTA,
    "blue":    curses.COLOR_BLUE,
    "green":   curses.COLOR_GREEN,
    "teal":    curses.COLOR_CYAN,
    "yellow":  curses.COLOR_YELLOW,
    "peach":   curses.COLOR_YELLOW,
    "red":     curses.COLOR_RED,
    "pink":    curses.COLOR_MAGENTA,
    "lavender":curses.COLOR_CYAN,
    "text":    curses.COLOR_WHITE,
    "subtext": curses.COLOR_WHITE,
    "base":    curses.COLOR_BLACK,
    "surface": curses.COLOR_BLACK,
    "overlay": curses.COLOR_BLACK,
}

# Color pair definitions: (name, fg_key, bg_key)
_PAIR_DEFS: List[Tuple[str, str, str]] = [
    ("logo",        "mauve",    "surface"),
    ("phi_good",    "green",    "base"),
    ("phi_warn",    "yellow",   "base"),
    ("phi_bad",     "red",      "base"),
    ("phi_hdr_g",   "green",    "surface"),
    ("phi_hdr_w",   "yellow",   "surface"),
    ("phi_hdr_r",   "red",      "surface"),
    ("regime_s",    "blue",     "surface"),
    ("regime_a",    "green",    "surface"),
    ("regime_h",    "peach",    "surface"),
    ("hdr_dim",     "subtext",  "surface"),
    ("tab_on",      "base",     "mauve"),
    ("tab_off",     "subtext",  "surface"),
    ("border",      "overlay",  "base"),
    ("bdr_hi",      "mauve",    "base"),
    ("text",        "text",     "base"),
    ("dim",         "subtext",  "base"),
    ("user_lbl",    "blue",     "base"),
    ("agent_lbl",   "pink",     "base"),
    ("sys_lbl",     "teal",     "base"),
    ("metric_k",    "lavender", "base"),
    ("metric_v",    "text",     "base"),
    ("up_bad",      "red",      "base"),
    ("down_good",   "green",    "base"),
    ("neutral",     "subtext",  "base"),
    ("sidebar_h",   "mauve",    "base"),
    ("input_bg",    "text",     "overlay"),
    ("cursor",      "base",     "mauve"),
    ("help_bg",     "text",     "overlay"),
    ("error",       "red",      "base"),
    ("regime_lbl_s","blue",     "base"),
    ("regime_lbl_a","green",    "base"),
    ("regime_lbl_h","peach",    "base"),
    ("agent_work",  "teal",     "base"),
    ("agent_done",  "green",    "base"),
    ("agent_err",   "red",      "base"),
    ("skill_on",    "yellow",   "base"),
    ("skill_off",   "subtext",  "base"),
    ("feed_hdr",    "lavender", "surface"),
    ("agent_name",  "pink",     "base"),
    ("code_hdr",    "base",     "mauve"),
    ("code_ln",     "subtext",  "base"),
    ("code_kw",     "blue",     "base"),
    ("code_str",    "green",    "base"),
    ("code_fn",     "pink",     "base"),
    ("code_cls",    "mauve",    "base"),
    ("code_imp",    "lavender", "base"),
    ("code_cmt",    "subtext",  "base"),
    ("code_flow",   "peach",    "base"),
    ("code_sel",    "text",     "overlay"),
    ("tree_dir",    "yellow",   "base"),
    ("tree_file",   "text",     "base"),
    ("tree_sel",    "base",     "teal"),
    ("peach_lbl",   "peach",    "base"),
    ("teal_lbl",    "teal",     "base"),
    ("phi_warn",    "yellow",   "base"),
]

# Module-level pair number registry
_PAIRS: dict = {}
_HAS_256 = False


# ── Color setup ───────────────────────────────────────────────────────────────

def _setup_colors(stdscr) -> bool:
    """Init all color pairs. Try 256-color first; fall back to 8-color.
    Store pair numbers in module-level _PAIRS dict. Return True if 256-color."""
    global _PAIRS, _HAS_256

    if not curses.has_colors():
        _HAS_256 = False
        # Build dummy pairs so cp() doesn't crash
        for i, (name, _fg, _bg) in enumerate(_PAIR_DEFS, start=1):
            _PAIRS[name] = 0
        return False

    curses.start_color()
    curses.use_default_colors()

    has_256 = curses.COLORS >= 256

    for i, (name, fg_key, bg_key) in enumerate(_PAIR_DEFS, start=1):
        try:
            if has_256:
                fg = _MOCHA[fg_key]
                bg = _MOCHA[bg_key]
            else:
                fg = _FALLBACK_8.get(fg_key, curses.COLOR_WHITE)
                bg = _FALLBACK_8.get(bg_key, curses.COLOR_BLACK)
            curses.init_pair(i, fg, bg)
            _PAIRS[name] = i
        except curses.error:
            _PAIRS[name] = 0

    _HAS_256 = has_256
    return has_256


def cp(name: str, bold: bool = False) -> int:
    """Return curses color pair attribute, optionally bold."""
    pair_num = _PAIRS.get(name, 0)
    attr = curses.color_pair(pair_num)
    if bold:
        attr |= curses.A_BOLD
    return attr


# ── Safe drawing helpers ───────────────────────────────────────────────────────

def _safe_addstr(win, y: int, x: int, text: str, attr: int = 0) -> None:
    """Draw text clipped to window bounds, swallowing all curses errors."""
    if not text:
        return
    try:
        h, w = win.getmaxyx()
        if y < 0 or y >= h or x >= w:
            return
        avail = w - x
        if avail <= 0:
            return
        clipped = text[:avail]
        win.addstr(y, x, clipped, attr)
    except curses.error:
        pass


def _fill_line(win, y: int, attr: int = 0) -> None:
    """Fill entire row y with spaces using the given attribute."""
    try:
        h, w = win.getmaxyx()
        if y < 0 or y >= h:
            return
        win.addstr(y, 0, " " * w, attr)
    except curses.error:
        try:
            h, w = win.getmaxyx()
            if y < 0 or y >= h or w <= 0:
                return
            win.addstr(y, 0, " " * (w - 1), attr)
        except curses.error:
            pass


# ── Data model ────────────────────────────────────────────────────────────────

class Role(Enum):
    USER   = "YOU"
    AGENT  = "AGENT"
    SYSTEM = "SYS"


@dataclass
class Message:
    role: Role
    text: str
    phi: Optional[float] = None
    ts: float = field(default_factory=time.time)


@dataclass
class AgentEvent:
    """Tracks one unit of agent work for the live activity feed."""
    ts: float
    agent: str        # "Refactor", "Quality", "Skill", "Chat", …
    action: str       # short description of what it did
    tool: str         # tool or skill invoked (empty if none)
    phi_delta: float  # Φ change from this action (0.0 if not applicable)
    status: str       # "working" | "done" | "error"


class Tab(Enum):
    CHAT    = 0
    METRICS = 1
    THEORY  = 2
    HISTORY = 3
    AGENTS  = 4
    CODE    = 5


@dataclass
class AppState:
    engine: RegimeEngine
    messages: List[Message]
    tab: Tab = Tab.CHAT
    input_buf: str = ""
    chat_scroll: int = 0
    show_help: bool = False
    error: Optional[str] = None
    _agent: object = None          # lazy NeuralAgent
    agent_events: List[AgentEvent] = field(default_factory=list)
    active_skills: List[dict] = field(default_factory=list)
    filetree: Optional[FileTree] = None   # connected directory
    file_selected: int = 0                # selected index in file tree
    file_scroll: int = 0                  # code viewer scroll offset
    tree_scroll: int = 0                  # file tree scroll offset


# ── Header ────────────────────────────────────────────────────────────────────

def draw_header(stdscr, state: AppState) -> None:
    """Draw rows 0 and 1: logo/phi/regime bar, then tabs."""
    h, w = stdscr.getmaxyx()
    if h < 2:
        return

    m = state.engine.metrics

    # ── Row 0: logo + Φ + regime ──────────────────────────────────────────────
    _fill_line(stdscr, 0, cp("hdr_dim"))

    logo = "⚡ DEEP AGENT STORM SWARM"
    _safe_addstr(stdscr, 0, 1, logo, cp("logo", bold=True))

    # Φ value — color depends on magnitude
    phi = m.phi if m else 0.0
    if phi >= 0:
        phi_pair = "phi_hdr_g"
        dot = "●"
    elif phi > -2.0:
        phi_pair = "phi_hdr_w"
        dot = "○"
    else:
        phi_pair = "phi_hdr_r"
        dot = "◌"

    phi_str = f"Φ={phi:+.4f} {dot}"
    phi_x = max(len(logo) + 4, (w - len(phi_str)) // 2)
    _safe_addstr(stdscr, 0, phi_x, phi_str, cp(phi_pair, bold=True))

    # Regime badge — right-aligned
    regime = m.regime if m else "hybrid"
    if regime == "simple":
        regime_pair = "regime_s"
        badge = " SIMPLE "
    elif regime == "advanced":
        regime_pair = "regime_a"
        badge = " ADVANCED "
    else:
        regime_pair = "regime_h"
        badge = " HYBRID "

    version = "v0.2"
    right_text = f" {version}  {badge}"
    badge_start = w - len(right_text) - 1
    if badge_start > 0:
        _safe_addstr(stdscr, 0, badge_start, f" {version}  ", cp("hdr_dim"))
        _safe_addstr(stdscr, 0, badge_start + len(f" {version}  "), badge, cp(regime_pair, bold=True))

    # ── Row 1: tab bar ────────────────────────────────────────────────────────
    _fill_line(stdscr, 1, cp("hdr_dim"))

    tabs_info = [
        (Tab.CHAT,    "1 CHAT ★"),
        (Tab.METRICS, "2 METRICS"),
        (Tab.THEORY,  "3 THEORY"),
        (Tab.HISTORY, "4 HISTORY"),
        (Tab.AGENTS,  "5 AGENTS"),
        (Tab.CODE,    "6 CODE"),
    ]

    col = 1
    for tab_enum, label in tabs_info:
        active = (state.tab == tab_enum)
        tag = f"[{label}]"
        pair = cp("tab_on", bold=True) if active else cp("tab_off")
        _safe_addstr(stdscr, 1, col, tag, pair)
        col += len(tag) + 2


# ── Sidebar ───────────────────────────────────────────────────────────────────

def draw_sidebar(stdscr, state: AppState, top: int, bottom: int, col: int) -> None:
    """Draw the right-side metrics panel starting at column col, rows top..bottom-1."""
    h, w = stdscr.getmaxyx()
    m = state.engine.metrics
    if m is None:
        return

    sidebar_w = w - col
    if sidebar_w < 2:
        return

    def _sline(row: int, text: str, attr: int = 0) -> None:
        if row >= bottom:
            return
        # Clear the row segment first
        try:
            stdscr.addstr(row, col, " " * sidebar_w, cp("dim"))
        except curses.error:
            pass
        _safe_addstr(stdscr, row, col + 1, text, attr)

    def _section(row: int, title: str) -> int:
        _sline(row, title, cp("sidebar_h", bold=True))
        return row + 1

    def _blank(row: int) -> int:
        _sline(row, "")
        return row + 1

    row = top

    # ── LIVE Φ(G) ─────────────────────────────────────────────────────────────
    row = _section(row, "── LIVE Φ(G) ─────")

    phi = m.phi
    if phi >= 0:
        phi_pair = cp("phi_good", bold=True)
        dot = "●"
    elif phi > -2.0:
        phi_pair = cp("phi_warn", bold=True)
        dot = "○"
    else:
        phi_pair = cp("phi_bad", bold=True)
        dot = "◌"

    phi_line = f"{phi:+.4f} {dot}"
    _sline(row, phi_line, phi_pair)
    row += 1
    row = _blank(row)

    # Arrow helper
    def _arrow(val: float, prev: float = 0.0) -> Tuple[str, str]:
        diff = val - prev
        if abs(diff) < 0.001:
            return "→", "neutral"
        return ("↑", "down_good") if diff > 0 else ("↓", "up_bad")

    # Use metrics directly — no prev tracking, show stable arrows
    q = m.q
    coupling = m.coupling
    mean_v = m.mean_v

    # Q row — higher is better
    q_arrow = "↑" if q > 0.3 else "→"
    q_arrow_pair = "down_good" if q > 0.3 else "neutral"
    _sline(row, f"Q  {q:+.4f}  ", cp("metric_k"))
    _safe_addstr(stdscr, row, col + 11, q_arrow, cp(q_arrow_pair, bold=True))
    row += 1

    # Č row — lower is better
    c_arrow = "↓" if coupling < 0.5 else "↑"
    c_arrow_pair = "down_good" if coupling < 0.5 else "up_bad"
    high_tag = "  HIGH" if coupling > 0.7 else ""
    _sline(row, f"Č  {coupling:+.4f}  ", cp("metric_k"))
    _safe_addstr(stdscr, row, col + 11, c_arrow, cp(c_arrow_pair, bold=True))
    if high_tag:
        _safe_addstr(stdscr, row, col + 13, high_tag, cp("up_bad", bold=True))
    row += 1

    # V row — lower is better
    v_arrow = "↓" if mean_v < 4.0 else "→"
    v_arrow_pair = "down_good" if mean_v < 4.0 else "neutral"
    _sline(row, f"V  {mean_v:+.4f}  ", cp("metric_k"))
    _safe_addstr(stdscr, row, col + 11, v_arrow, cp(v_arrow_pair, bold=True))
    row += 1

    row = _blank(row)

    # ── BREAKDOWN ─────────────────────────────────────────────────────────────
    row = _section(row, "── BREAKDOWN ────")
    coeffs = Regime.coeffs(state.engine.current_regime)
    alpha_q = coeffs.alpha * q
    beta_c  = -coeffs.beta * coupling
    gamma_v = -coeffs.gamma * mean_v
    _sline(row, f"α·Q  {alpha_q:+.4f}", cp("metric_v"))
    row += 1
    _sline(row, f"-β·Č {beta_c:+.4f}", cp("metric_v"))
    row += 1
    _sline(row, f"-γ·V {gamma_v:+.4f}", cp("metric_v"))
    row += 1
    row = _blank(row)

    # ── REGIME ────────────────────────────────────────────────────────────────
    row = _section(row, "── REGIME ──────")
    regime = state.engine.current_regime
    if regime == "simple":
        reg_pair = "regime_lbl_s"
    elif regime == "advanced":
        reg_pair = "regime_lbl_a"
    else:
        reg_pair = "regime_lbl_h"
    _sline(row, regime.upper(), cp(reg_pair, bold=True))
    row += 1
    _sline(row, f"α={coeffs.alpha} β={coeffs.beta} γ={coeffs.gamma}", cp("dim"))
    row += 1
    row = _blank(row)

    # ── GRAPH ─────────────────────────────────────────────────────────────────
    row = _section(row, "── GRAPH ───────")
    _sline(row, f"{m.n_nodes} nodes · {m.n_edges} edges", cp("metric_v"))
    row += 1
    _sline(row, f"{m.n_modules} modules", cp("dim"))
    row += 1
    n_trans = len(state.engine.transitions)
    _sline(row, f"{n_trans} transitions", cp("dim"))
    row += 1
    row = _blank(row)

    # ── ACTIVE SKILLS ─────────────────────────────────────────────────────────
    if row < bottom - 2:
        row = _section(row, "── SKILLS ──────")
        if state.active_skills:
            for sk in state.active_skills[:3]:
                if row >= bottom - 1:
                    break
                sid = sk.get("id", "?")
                _sline(row, f"★ {sid}", cp("skill_on", bold=True))
                row += 1
        else:
            _sline(row, "none active", cp("skill_off"))
            row += 1
        row = _blank(row)

    # ── LAST AGENT EVENT ──────────────────────────────────────────────────────
    if state.agent_events and row < bottom - 2:
        row = _section(row, "── LAST EVENT ──")
        ev = state.agent_events[-1]
        status_pair = "agent_done" if ev.status == "done" else ("agent_err" if ev.status == "error" else "agent_work")
        _sline(row, ev.agent[:16], cp("agent_name", bold=True))
        row += 1
        if row < bottom - 1:
            action_short = ev.action[:sidebar_w - 3]
            _sline(row, action_short, cp(status_pair))
            row += 1
        if row < bottom - 1 and ev.tool:
            _sline(row, f"  {ev.tool[:sidebar_w - 5]}", cp("skill_on"))
            row += 1
        if row < bottom - 1 and ev.phi_delta != 0.0:
            delta_pair = "down_good" if ev.phi_delta > 0 else "up_bad"
            _sline(row, f"  ΔΦ {ev.phi_delta:+.4f}", cp(delta_pair, bold=True))
            row += 1
        row = _blank(row)

    # Fill remaining rows
    while row < bottom - 2:
        _sline(row, "")
        row += 1

    # Bottom hints
    if row < bottom - 1:
        _sline(row, "[r] refresh  [?] help", cp("dim"))
        row += 1
    if row < bottom:
        _sline(row, "[q] quit  [1-5] tabs", cp("dim"))


# ── Chat line builder ─────────────────────────────────────────────────────────

def _build_chat_lines(state: AppState, width: int) -> List[Tuple[str, str, bool]]:
    """Build flat list of (text, pair_name, bold) for all messages."""
    lines: List[Tuple[str, str, bool]] = []
    wrap_width = max(10, width - 3)

    for msg in state.messages:
        # Role label
        if msg.role == Role.USER:
            lines.append(("YOU ▸", "user_lbl", True))
        elif msg.role == Role.AGENT:
            if msg.phi is not None:
                lines.append((f"AGENT ▸  Φ={msg.phi:+.4f}", "agent_lbl", True))
            else:
                lines.append(("AGENT ▸", "agent_lbl", True))
        else:  # SYSTEM
            lines.append(("─── SYS ───────────────────────", "sys_lbl", False))

        # Body lines
        _METRIC_PREFIXES = (
            "Φ(", "Q=", "Č=", "V=",
            "α", "β", "γ",
            "══", "──",
            "Phi(", "alpha", "beta", "gamma",
        )

        for raw_line in msg.text.splitlines():
            if not raw_line:
                lines.append(("", "text", False))
                continue
            wrapped = textwrap.wrap(raw_line, wrap_width) or [""]
            for wline in wrapped:
                indented = "  " + wline
                if msg.role == Role.SYSTEM:
                    pair = "dim"
                elif any(wline.startswith(p) for p in _METRIC_PREFIXES):
                    pair = "metric_k"
                else:
                    pair = "text"
                lines.append((indented, pair, False))

        # Spacer between messages
        lines.append(("", "text", False))

    return lines


# ── Chat panel ────────────────────────────────────────────────────────────────

def draw_chat(stdscr, state: AppState, top: int, bottom: int, right: int) -> None:
    """Draw the chat panel from rows top..bottom-1, columns 0..right-1."""
    h, w = stdscr.getmaxyx()
    panel_w = min(right, w)
    if panel_w < 4 or bottom <= top:
        return

    chat_lines = _build_chat_lines(state, panel_w)
    total = len(chat_lines)
    visible = bottom - top

    # chat_scroll=0 means bottom; higher means scrolled back
    scroll = state.chat_scroll
    # Start index into chat_lines for the visible window
    if scroll == 0:
        start = max(0, total - visible)
    else:
        start = max(0, total - visible - scroll)

    for row_offset in range(visible):
        screen_row = top + row_offset
        line_idx = start + row_offset
        # Clear line first
        try:
            stdscr.addstr(screen_row, 0, " " * panel_w, cp("text"))
        except curses.error:
            pass

        if line_idx < total:
            text, pair_name, bold = chat_lines[line_idx]
            if text:
                _safe_addstr(stdscr, screen_row, 0, text, cp(pair_name, bold=bold))


# ── Full metrics tab ──────────────────────────────────────────────────────────

def draw_full_metrics(stdscr, state: AppState, top: int, bottom: int) -> None:
    """Tab.METRICS full view."""
    h, w = stdscr.getmaxyx()
    m = state.engine.metrics
    if m is None:
        return

    coeffs = Regime.coeffs(state.engine.current_regime)
    alpha_q  = coeffs.alpha * m.q
    beta_c   = coeffs.beta  * m.coupling
    gamma_v  = coeffs.gamma * m.mean_v
    phi_calc = alpha_q - beta_c - gamma_v

    phi_pair = "phi_good" if m.phi >= 0 else ("phi_warn" if m.phi > -2.0 else "phi_bad")

    rows = [
        ("", "text", False),
        ("═══ LIVE Φ(G) BREAKDOWN ════════════════════", "metric_k", True),
        ("", "text", False),
        (f"  Objective:  Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)", "metric_k", False),
        ("", "text", False),
        (f"  Regime: {state.engine.current_regime.upper()}", "text", True),
        (f"  α={coeffs.alpha}  β={coeffs.beta}  γ={coeffs.gamma}", "dim", False),
        ("", "text", False),
        ("─── METRICS ──────────────────────────────", "metric_k", False),
        (f"  Q(G)    = {m.q:.4f}     (modularity — higher is better)", "metric_v", False),
        (f"  Č(G)   = {m.coupling:.4f}     (coupling — lower is better)", "metric_v", False),
        (f"  mean(V) = {m.mean_v:.4f}     (cyclomatic complexity — lower is better)", "metric_v", False),
        (f"  max(V)  = {m.max_v:.4f}", "metric_v", False),
        (f"  quality = {m.quality:.4f}", "metric_v", False),
        ("", "text", False),
        ("─── COMPONENT BREAKDOWN ─────────────────", "metric_k", False),
        (f"  α·Q(G)    = {coeffs.alpha} × {m.q:.4f} = {alpha_q:+.4f}", "metric_v", False),
        (f"  β·Č(G)   = {coeffs.beta} × {m.coupling:.4f} = {beta_c:+.4f}  (subtracted)", "metric_v", False),
        (f"  γ·mean(V) = {coeffs.gamma} × {m.mean_v:.4f} = {gamma_v:+.4f}  (subtracted)", "metric_v", False),
        ("  " + "─" * 38, "metric_k", False),
        (f"  Φ(G)     = {phi_calc:+.4f}", phi_pair, True),
        ("", "text", False),
        ("─── REGIME SWEEP ───────────────────────", "metric_k", False),
    ]

    # Regime sweep
    sweep = state.engine.sweep_regimes()
    best_r, best_phi = max(sweep, key=lambda x: x[1])
    for r, phi in sweep:
        marker = " ← BEST" if r == best_r else ""
        active = " [current]" if r == state.engine.current_regime else ""
        rl = "regime_lbl_s" if r == "simple" else ("regime_lbl_a" if r == "advanced" else "regime_lbl_h")
        rows.append((f"  {r.upper():10s}  Φ={phi:+.4f}{marker}{active}", rl, r == state.engine.current_regime))

    rows += [
        ("", "text", False),
        ("─── GRAPH TOPOLOGY ───────────────────", "metric_k", False),
        (f"  {m.n_nodes} nodes  ·  {m.n_edges} edges  ·  {m.n_modules} modules", "metric_v", False),
        (f"  {len(state.engine.transitions)} regime transitions in history", "dim", False),
        ("", "text", False),
        ("  Type /metrics to refresh  ·  [r] to auto-refresh", "dim", False),
    ]

    visible = bottom - top
    for row_offset in range(visible):
        screen_row = top + row_offset
        _fill_line(stdscr, screen_row, cp("text"))
        if row_offset < len(rows):
            text, pair_name, bold = rows[row_offset]
            if text:
                _safe_addstr(stdscr, screen_row, 0, text, cp(pair_name, bold=bold))


# ── Theory tab ────────────────────────────────────────────────────────────────

def draw_theory(stdscr, state: AppState, top: int, bottom: int) -> None:
    """Tab.THEORY: full mathematical explanation."""
    theory_text = state.engine.theory_explain()
    theory_lines = theory_text.split("\n")

    _METRIC_PREFIXES = (
        "Φ", "Q(", "Č(", "mean(", "max(", "=", "═", "─",
        "OBJECTIVE", "CURRENT", "COEFFICIENTS", "LIVE", "COMPONENT", "alpha",
    )

    visible = bottom - top
    for row_offset in range(visible):
        screen_row = top + row_offset
        _fill_line(stdscr, screen_row, cp("text"))
        if row_offset < len(theory_lines):
            line = theory_lines[row_offset]
            stripped = line.strip()
            if any(stripped.startswith(p) for p in _METRIC_PREFIXES) or "═" in line or "─" in line:
                pair = "metric_k"
            else:
                pair = "text"
            if line:
                _safe_addstr(stdscr, screen_row, 0, line, cp(pair))


# ── History tab ───────────────────────────────────────────────────────────────

def draw_history(stdscr, state: AppState, top: int, bottom: int) -> None:
    """Tab.HISTORY: show all regime transitions."""
    h, w = stdscr.getmaxyx()

    rows = [
        "",
        "═══ REGIME TRANSITION HISTORY ═════════════════",
        "",
    ]

    if not state.engine.transitions:
        rows.append("  No transitions yet. Use /switch <regime> or wait for auto-detection.")
    else:
        for i, t in enumerate(state.engine.transitions, start=1):
            delta = t.improvement()
            delta_str = f"{delta:+.4f}"
            rows.append(f"  #{i:02d}  {t.from_} → {t.to}  |  Φ: {t.phi_before:+.4f} → {t.phi_after:+.4f}  ({delta_str})")
            rows.append(f"       Reason: {t.reason}")
            rows.append("")

    rows += [
        "─── METRIC HISTORY ──────────────────────",
        f"  {len(state.engine.history)} snapshots recorded",
        "",
    ]

    if state.engine.history:
        rows.append("  Last 5 Φ(G) readings:")
        recent = state.engine.history[-5:]
        for snap_dict in recent:
            phi_val = snap_dict.get("phi", 0.0)
            reg_val = snap_dict.get("regime", "?")
            rows.append(f"    Φ={phi_val:+.4f}  [{reg_val}]")

    visible = bottom - top
    for row_offset in range(visible):
        screen_row = top + row_offset
        _fill_line(stdscr, screen_row, cp("text"))
        if row_offset < len(rows):
            line = rows[row_offset]
            if not line:
                continue
            # Color transitions based on delta sign
            if line.startswith("  #") and "(" in line:
                # Check delta
                try:
                    delta_part = line.split("(")[-1].rstrip(")")
                    delta_val = float(delta_part)
                    pair = "down_good" if delta_val > 0 else "up_bad"
                except Exception:
                    pair = "text"
            elif "═" in line or "─" in line:
                pair = "metric_k"
            else:
                pair = "text"
            _safe_addstr(stdscr, screen_row, 0, line, cp(pair))


# ── Agents tab ────────────────────────────────────────────────────────────────

_AGENT_EMOJIS = {
    "Refactor":  "⚙",
    "Quality":   "◈",
    "Test":      "✓",
    "Skill":     "★",
    "Repo":      "⎇",
    "Build":     "⬡",
    "Planner":   "◉",
    "Chat":      "◆",
    "Swarm":     "⚡",
    "System":    "·",
}


def draw_agents_tab(stdscr, state: AppState, top: int, bottom: int) -> None:
    """Tab.AGENTS: live agent activity feed + active skills."""
    h, w = stdscr.getmaxyx()
    visible = bottom - top

    def _aline(row_offset: int, text: str, attr: int = 0) -> None:
        screen_row = top + row_offset
        if screen_row >= bottom or screen_row >= h:
            return
        _fill_line(stdscr, screen_row, cp("text"))
        if text:
            _safe_addstr(stdscr, screen_row, 0, text, attr)

    row = 0

    # ── Header ────────────────────────────────────────────────────────────────
    _aline(row, "  ══ AGENT ACTIVITY FEED ══════════════════════════════", cp("feed_hdr", bold=True))
    row += 1
    _aline(row, "", cp("text"))
    row += 1

    # ── Column header (adaptive to terminal width) ────────────────────────────
    _aline(row, f"  {'AGENT':<14} ACTION{'ΔΦ':>{max(4, w - 22)}}  ", cp("metric_k", bold=True))
    row += 1
    _aline(row, "  " + "─" * max(4, w - 4), cp("dim"))
    row += 1

    # ── Events (newest first) ─────────────────────────────────────────────────
    events = list(reversed(state.agent_events))
    if not events:
        _aline(row, "  No agent activity yet.", cp("dim"))
        _aline(row + 1, "  Run /swarm <task> or type anything to see agents at work.", cp("dim"))
        row += 2
    else:
        for ev in events:
            if row >= visible - 6:
                remaining = len(events) - events.index(ev)
                if remaining > 0:
                    _aline(row, f"  … {remaining} older events (scroll up)", cp("dim"))
                break
            status_pair = (
                "agent_done" if ev.status == "done"
                else "agent_err" if ev.status == "error"
                else "agent_work"
            )
            status_icon = "✓" if ev.status == "done" else ("✗" if ev.status == "error" else "…")
            icon = _AGENT_EMOJIS.get(ev.agent, "·")
            _safe_addstr(stdscr, top + row, 0, " " * w, cp("text"))

            # Adaptive columns: agent(16) | action(rest-24) | ΔΦ(10) | status(2)
            agent_w  = 16
            delta_w  = 10
            status_w = 3
            action_w = max(8, w - agent_w - delta_w - status_w - 2)

            action_col = ev.action[:action_w]
            delta_col  = f"{ev.phi_delta:+.4f}" if ev.phi_delta != 0.0 else ""

            _safe_addstr(stdscr, top + row, 0,  f"  {icon} ", cp("agent_name"))
            _safe_addstr(stdscr, top + row, 4,  f"{ev.agent:<{agent_w - 4}}", cp("agent_name", bold=True))
            _safe_addstr(stdscr, top + row, agent_w, f"{action_col}", cp(status_pair))
            if delta_col:
                dpair = "down_good" if ev.phi_delta > 0 else "up_bad"
                _safe_addstr(stdscr, top + row, w - status_w - delta_w,
                             f"{delta_col:>{delta_w}}", cp(dpair, bold=True))
            _safe_addstr(stdscr, top + row, w - status_w,
                         f" {status_icon}", cp(status_pair, bold=True))
            row += 1

            # Tool / skill on its own indented line (always fits)
            if ev.tool and row < visible - 6:
                tool_avail = max(10, w - 6)
                tool_display = ev.tool[:tool_avail]
                pair = "skill_on" if ev.tool.startswith("skill:") else "dim"
                prefix = "  ★" if ev.tool.startswith("skill:") else "  ·"
                _aline(row, f"{prefix} {tool_display}", cp(pair))
                row += 1

    # ── Separator ─────────────────────────────────────────────────────────────
    if row < visible - 2:
        _aline(row, "", cp("text"))
        row += 1
        _aline(row, "  ══ ACTIVE SKILLS (triggered by current metrics) ═══════", cp("feed_hdr", bold=True))
        row += 1

    # ── Active skills ─────────────────────────────────────────────────────────
    try:
        from .skills import SkillManager
        sm = SkillManager()
        snap = state.engine.snapshot()
        all_skills = sm._yaml_skills + list(sm.skills.values())
        active_ids = {s.get("id") for s in sm.match_metrics(snap)}

        # Update state's active_skills list
        state.active_skills = sm.match_metrics(snap)

        if not all_skills:
            _aline(row, "  No skills loaded.", cp("dim"))
            row += 1
        else:
            for sk in all_skills:
                if row >= visible - 1:
                    break
                if isinstance(sk, dict):
                    sid   = sk.get("id", "?")
                    sname = sk.get("name", sid)
                    sdesc = sk.get("description", "")
                    trigger = sk.get("trigger", {})
                    if isinstance(trigger, dict):
                        metric = trigger.get("metric", "")
                        op     = trigger.get("operator", ">")
                        thresh = trigger.get("threshold", 0)
                        trig_str = f"{metric} {op} {thresh}"
                    else:
                        trig_str = str(trigger)
                else:
                    sid      = sk.name
                    sname    = sk.name
                    sdesc    = sk.description
                    trig_str = sk.trigger

                is_active = sid in active_ids
                pair      = "skill_on" if is_active else "skill_off"
                marker    = "★ ACTIVE" if is_active else "  ·    "

                # Line 1: marker + name (full, never truncated at fixed col)
                name_avail = max(10, w - 12)
                name_display = sname[:name_avail]
                _safe_addstr(stdscr, top + row, 0, " " * w, cp("text"))
                _safe_addstr(stdscr, top + row, 2, marker, cp(pair, bold=is_active))
                _safe_addstr(stdscr, top + row, 12, name_display,
                             cp(pair, bold=is_active))
                row += 1
                if row >= visible - 1:
                    break

                # Line 2: trigger condition + skill id (indented)
                trig_avail = max(10, w - 14)
                trig_display = f"[{sid}]  trigger: {trig_str}"[:trig_avail]
                _safe_addstr(stdscr, top + row, 0, " " * w, cp("text"))
                _safe_addstr(stdscr, top + row, 14, trig_display, cp("dim"))
                row += 1
                if row >= visible - 1:
                    break

                # Line 3 (active only): what it does
                if is_active and sdesc:
                    desc_avail = max(10, w - 8)
                    _safe_addstr(stdscr, top + row, 0, " " * w, cp("text"))
                    _safe_addstr(stdscr, top + row, 6,
                                 f"→ {sdesc[:desc_avail]}", cp("agent_done"))
                    row += 1
                    if row >= visible - 1:
                        break

                # Blank line between skills
                _aline(row, "")
                row += 1
    except Exception as e:
        _aline(row, f"  Skills unavailable: {e}", cp("error"))
        row += 1

    # Fill remaining
    while row < visible:
        _aline(row, "", cp("text"))
        row += 1


# ── Code tab ──────────────────────────────────────────────────────────────────

_COLOR_MAP = {
    'dim':          'code_cmt',
    'phi_good':     'code_str',
    'regime_lbl_s': 'code_imp',
    'agent_lbl':    'code_fn',
    'sidebar_h':    'code_cls',
    'peach_lbl':    'code_flow',
    'teal_lbl':     'code_flow',
    'lavender':     'code_flow',
    'phi_warn':     'phi_warn',
    'text':         'text',
}


def _syntax_pair(line: str, ext: str) -> int:
    """Return curses color attr for a source line."""
    raw = color_line(line, ext)
    pair_name = _COLOR_MAP.get(raw, 'text')
    return cp(pair_name)


def draw_code_tab(stdscr, state: AppState, top: int, bottom: int) -> None:
    """Tab.CODE — file tree (left) + syntax-highlighted code viewer (right)."""
    h, w = stdscr.getmaxyx()
    visible = bottom - top

    def _cline(row_offset: int, text: str, attr: int = 0, col: int = 0) -> None:
        screen_row = top + row_offset
        if screen_row >= bottom or screen_row >= h:
            return
        try:
            stdscr.addstr(screen_row, col, " " * max(0, w - col), cp("text"))
        except curses.error:
            pass
        if text:
            _safe_addstr(stdscr, screen_row, col, text, attr)

    ft = state.filetree

    # ── No directory connected ─────────────────────────────────────────────────
    if ft is None:
        _cline(0, "  ══ CODE VIEWER ══════════════════════════════════════", cp("code_hdr", bold=True))
        _cline(1, "", 0)
        _cline(2, "  No directory connected.", cp("dim"))
        _cline(3, "", 0)
        _cline(4, "  Connect to your file system:", cp("text"))
        _cline(5, "    /connect ~              → your Termux home", cp("code_imp"))
        _cline(6, "    /connect ~/projects     → projects folder", cp("code_imp"))
        _cline(7, "    /connect /sdcard        → Android storage", cp("code_imp"))
        _cline(8, "", 0)
        _cline(9, "  Then agents can read, write, and modify files.", cp("dim"))
        _cline(10, "  Type /connect <path> in the CHAT tab.", cp("dim"))
        _cline(11, "", 0)
        if state.agent_events:
            _cline(12, "  ── Recent agent writes ───────────────────────", cp("feed_hdr"))
            row = 13
            for ev in reversed(state.agent_events):
                if row >= visible - 1:
                    break
                if ev.tool and ('write' in ev.action or 'create' in ev.action.lower()):
                    _cline(row, f"  [{ev.agent}] {ev.action}", cp("agent_done"))
                    row += 1
        for r in range(12, visible):
            _cline(r, "", 0)
        return

    # ── Layout: tree panel (left) | code panel (right) ────────────────────────
    tree_w = min(28, max(18, w // 5))
    code_start = tree_w + 1

    # ── File tree panel ────────────────────────────────────────────────────────
    files = ft.files
    total_files = len(files)

    for r in range(visible):
        screen_row = top + r
        if screen_row >= h:
            break
        try:
            stdscr.addstr(screen_row, 0, " " * tree_w, cp("text"))
        except curses.error:
            pass

    # Tree header
    root_short = ft.root[-tree_w + 4:] if len(ft.root) > tree_w - 4 else ft.root
    _safe_addstr(stdscr, top, 0, f" {root_short}"[:tree_w], cp("code_hdr", bold=True))

    # Vertical divider
    for r in range(visible):
        screen_row = top + r
        if screen_row < h:
            _safe_addstr(stdscr, screen_row, tree_w, "│", cp("border"))

    # File list
    tree_visible = visible - 1
    tree_start = state.tree_scroll

    for i in range(tree_visible):
        idx = tree_start + i
        screen_row = top + 1 + i
        if screen_row >= bottom or screen_row >= h:
            break
        try:
            stdscr.addstr(screen_row, 0, " " * tree_w, cp("text"))
        except curses.error:
            pass
        if idx >= total_files:
            continue

        fpath = files[idx]
        depth = fpath.count(os.sep)
        fname = os.path.basename(fpath)
        indent = "  " * min(depth, 3)
        is_open = (fpath == ft.open_path)
        is_sel = (idx == state.file_selected)

        prefix = "▶ " if is_open else "  "
        display = f"{indent}{prefix}{fname}"[:tree_w - 1]

        if is_sel:
            attr = cp("tree_sel", bold=True)
        elif is_open:
            attr = cp("code_fn", bold=True)
        elif fname.endswith('.py'):
            attr = cp("code_imp")
        elif fname.endswith(('.rs', '.go', '.c', '.cpp')):
            attr = cp("peach_lbl")
        elif fname.endswith(('.md', '.txt')):
            attr = cp("code_cmt")
        else:
            attr = cp("tree_file")

        _safe_addstr(stdscr, screen_row, 0, display, attr)

    # ── Code viewer panel ──────────────────────────────────────────────────────
    open_path = ft.open_path
    content = ft.content(open_path) if open_path else None

    code_w = max(10, w - code_start)

    if content is None:
        # No file open — show last write event or prompt
        for r in range(visible):
            screen_row = top + r
            if screen_row >= h:
                break
            try:
                stdscr.addstr(screen_row, code_start, " " * code_w, cp("text"))
            except curses.error:
                pass

        _safe_addstr(stdscr, top, code_start,
                     " ── Select a file ─────────────────────────────"[:code_w],
                     cp("code_hdr", bold=True))

        row = 1
        if ft.events:
            _safe_addstr(stdscr, top + row, code_start, " Recent file events:", cp("dim"))
            row += 1
            for ev in reversed(ft.events[-8:]):
                if row >= visible:
                    break
                ts = time.strftime("%H:%M:%S", time.localtime(ev.ts))
                icon = "✎" if ev.action in ("write", "create") else "◎"
                line = f" {icon} [{ev.agent}] {ev.action}: {ev.path}"[:code_w]
                pair = "agent_done" if ev.action in ("write", "create") else "code_imp"
                _safe_addstr(stdscr, top + row, code_start, line, cp(pair))
                row += 1
        else:
            row += 1
            _safe_addstr(stdscr, top + row, code_start,
                         " /read <file> or press Enter on a file in the tree"[:code_w], cp("dim"))
        return

    # ── Render file content ────────────────────────────────────────────────────
    ext = os.path.splitext(open_path)[1].lower()
    lines = content.splitlines()
    total_lines = len(lines)

    # Header bar
    fname_short = open_path[-(code_w - 20):] if len(open_path) > code_w - 20 else open_path
    last_ev = next((e for e in reversed(ft.events) if e.path == open_path), None)
    agent_tag = f"  [by {last_ev.agent}]" if last_ev else ""
    hdr = f" {fname_short}{agent_tag} · {total_lines} lines"[:code_w]
    try:
        stdscr.addstr(top, code_start, hdr.ljust(code_w), cp("code_hdr", bold=True))
    except curses.error:
        pass

    # Code lines
    code_visible = visible - 1
    scroll = max(0, min(state.file_scroll, max(0, total_lines - code_visible)))
    ln_w = len(str(total_lines)) + 1

    for i in range(code_visible):
        screen_row = top + 1 + i
        if screen_row >= bottom or screen_row >= h:
            break

        try:
            stdscr.addstr(screen_row, code_start, " " * code_w, cp("text"))
        except curses.error:
            pass

        line_idx = scroll + i
        if line_idx >= total_lines:
            continue

        line = lines[line_idx]
        ln_str = f"{line_idx + 1:>{ln_w}} "

        # Line number
        _safe_addstr(stdscr, screen_row, code_start, ln_str, cp("code_ln"))

        # Syntax-colored line content
        content_x = code_start + len(ln_str)
        avail = code_w - len(ln_str)
        if avail > 0:
            display_line = line[:avail]
            attr = _syntax_pair(line, ext)
            _safe_addstr(stdscr, screen_row, content_x, display_line, attr)


# ── Divider ───────────────────────────────────────────────────────────────────

def draw_divider(stdscr, top: int, bottom: int, col: int) -> None:
    """Draw vertical divider at column col from rows top..bottom-1."""
    for row in range(top, bottom):
        _safe_addstr(stdscr, row, col, "│", cp("border"))


# ── Help overlay ──────────────────────────────────────────────────────────────

def draw_help_overlay(stdscr) -> None:
    """Draw centered help modal."""
    h, w = stdscr.getmaxyx()

    content = [
        "  DEEP AGENT STORM SWARM — HELP    ",
        "  ─────────────────────────────────",
        "  [1] CHAT   [2] METRICS           ",
        "  [3] THEORY [4] HISTORY           ",
        "  [5] AGENTS [6] CODE VIEWER       ",
        "  [r]   Refresh  [q] Quit          ",
        "  [↑↓]  Scroll / select file       ",
        "  [PgUp/Dn] Scroll code            ",
        "  [Enter] Open selected file       ",
        "  [?]   Toggle this help           ",
        "  ─────────────────────────────────",
        "  CHAT COMMANDS                    ",
        "  /metrics   Φ(G) breakdown        ",
        "  /sweep     Compare regimes        ",
        "  /skills    Show skills            ",
        "  /swarm <task>  Run swarm          ",
        "  /connect <path>  Connect FS       ",
        "  /ls        List files             ",
        "  /read <file>   Open file          ",
        "  /switch <r>  Change regime        ",
        "  ─────────────────────────────────",
        "  Press any key to close           ",
    ]

    box_h = len(content) + 2
    box_w = max(len(line) for line in content) + 4

    start_y = max(0, (h - box_h) // 2)
    start_x = max(0, (w - box_w) // 2)

    attr = cp("help_bg")

    # Draw box background
    for i in range(box_h):
        row = start_y + i
        if row >= h:
            break
        try:
            stdscr.addstr(row, start_x, " " * min(box_w, w - start_x), attr)
        except curses.error:
            pass

    # Top border
    try:
        stdscr.addstr(start_y, start_x, "┌" + "─" * (box_w - 2) + "┐", attr | curses.A_BOLD)
    except curses.error:
        pass

    # Content rows
    for i, line in enumerate(content):
        row = start_y + 1 + i
        if row >= h:
            break
        padded = "│" + line.ljust(box_w - 2) + "│"
        bold = i == 0 or "─" in line
        try:
            stdscr.addstr(row, start_x, padded, attr | (curses.A_BOLD if bold else 0))
        except curses.error:
            pass

    # Bottom border
    bot_row = start_y + box_h - 1
    if bot_row < h:
        try:
            stdscr.addstr(bot_row, start_x, "└" + "─" * (box_w - 2) + "┘", attr | curses.A_BOLD)
        except curses.error:
            pass


# ── Input bar ─────────────────────────────────────────────────────────────────

def draw_input(stdscr, state: AppState, row: int) -> None:
    """Draw the input bar at the given row."""
    h, w = stdscr.getmaxyx()
    if row >= h or row < 0:
        return

    _fill_line(stdscr, row, cp("input_bg"))

    prompt = " ▸ "
    _safe_addstr(stdscr, row, 0, prompt, cp("user_lbl", bold=True))

    hint = "[enter] send  [?] help  [q] quit"
    hint_x = max(0, w - len(hint) - 1)

    # Available width for input text
    input_start = len(prompt)
    cursor_x = hint_x - 2  # leave room for cursor block
    avail_for_text = max(0, cursor_x - input_start)

    # Show the tail of the input buffer that fits
    buf = state.input_buf
    if len(buf) > avail_for_text:
        buf_display = buf[-(avail_for_text):]
    else:
        buf_display = buf

    _safe_addstr(stdscr, row, input_start, buf_display, cp("input_bg"))

    # Cursor block
    cursor_pos = input_start + len(buf_display)
    _safe_addstr(stdscr, row, cursor_pos, " ", cp("cursor"))

    # Right-aligned hint
    _safe_addstr(stdscr, row, hint_x, hint, cp("dim"))

    if state.error:
        err_text = f" ! {state.error} "
        err_x = max(0, (w - len(err_text)) // 2)
        _safe_addstr(stdscr, row, err_x, err_text, cp("error", bold=True))


# ── Status bar ────────────────────────────────────────────────────────────────

def draw_status(stdscr, state: AppState, row: int) -> None:
    """Draw bottom status bar."""
    h, w = stdscr.getmaxyx()
    if row >= h or row < 0:
        return

    m = state.engine.metrics
    if m:
        status = f"═ {m.n_nodes}nodes · {m.n_edges}edges · regime:{m.regime} · Φ={m.phi:+.4f}"
    else:
        status = "═ Deep Agent Storm Swarm · Initializing..."

    _fill_line(stdscr, row, cp("hdr_dim"))
    _safe_addstr(stdscr, row, 0, status, cp("hdr_dim"))


# ── Full render frame ─────────────────────────────────────────────────────────

def render(stdscr, state: AppState) -> None:
    """Full repaint every frame."""
    h, w = stdscr.getmaxyx()

    # Minimum terminal size check
    if h < 10 or w < 40:
        stdscr.clear()
        _safe_addstr(stdscr, 0, 0, "Terminal too small (need 40x10)", cp("error", bold=True))
        stdscr.refresh()
        return

    # Fixed row positions
    main_top    = 2
    main_bottom = h - 2   # exclusive; row h-2 is input, h-1 is status
    input_row   = h - 2
    status_row  = h - 1

    if main_bottom <= main_top:
        return

    # Sidebar geometry
    sidebar_w = max(20, min(26, w // 4))
    divider_col = w - sidebar_w - 1
    chat_right = divider_col

    # ── Draw header rows ──────────────────────────────────────────────────────
    draw_header(stdscr, state)

    # ── Draw main content ─────────────────────────────────────────────────────
    if state.tab == Tab.CHAT:
        draw_chat(stdscr, state, main_top, main_bottom, chat_right)
        draw_divider(stdscr, main_top, main_bottom, divider_col)
        draw_sidebar(stdscr, state, main_top, main_bottom, divider_col + 1)

    elif state.tab == Tab.METRICS:
        draw_full_metrics(stdscr, state, main_top, main_bottom)

    elif state.tab == Tab.THEORY:
        draw_theory(stdscr, state, main_top, main_bottom)

    elif state.tab == Tab.HISTORY:
        draw_history(stdscr, state, main_top, main_bottom)

    elif state.tab == Tab.AGENTS:
        draw_agents_tab(stdscr, state, main_top, main_bottom)

    elif state.tab == Tab.CODE:
        draw_code_tab(stdscr, state, main_top, main_bottom)

    # ── Input + status ────────────────────────────────────────────────────────
    draw_input(stdscr, state, input_row)
    draw_status(stdscr, state, status_row)

    # ── Help overlay (drawn last, on top of everything) ───────────────────────
    if state.show_help:
        draw_help_overlay(stdscr)

    stdscr.refresh()


def _emit(state: AppState, agent: str, action: str, tool: str = "",
          phi_delta: float = 0.0, status: str = "done") -> None:
    """Append an agent event to the activity feed."""
    state.agent_events.append(AgentEvent(
        ts=time.time(), agent=agent, action=action,
        tool=tool, phi_delta=phi_delta, status=status,
    ))
    # Keep the feed bounded
    if len(state.agent_events) > 200:
        state.agent_events = state.agent_events[-200:]


def _run_swarm(state: AppState, task: str) -> str:
    """Run the 8-agent swarm and emit live events to the activity feed."""
    try:
        from .agent import Swarm
        from .skills import SkillManager
    except ImportError as e:
        return f"Swarm unavailable: {e}"

    engine = state.engine
    snap_before = engine.snapshot()
    phi_before = snap_before.get("phi", 0.0) if isinstance(snap_before, dict) else snap_before.phi

    _emit(state, "Swarm", f"task: {task[:40]}", "", 0.0, "working")

    # If file system connected, let agents read/scan the open file
    if state.filetree and state.filetree.open_path:
        open_file = state.filetree.open_path
        content = state.filetree.content(open_file)
        if content:
            _emit(state, "FileSystem", f"reading: {open_file}",
                  "read_file", 0.0, "done")
            # Crawl the connected directory into the engine graph
            try:
                from .crawler import CodebaseCrawler
                crawler = CodebaseCrawler()
                graph = crawler.crawl(state.filetree.root)
                engine.graph = graph
                engine.update_metrics()
                _emit(state, "Refactor", f"crawled: {len(graph.nodes)} nodes",
                      "crawl_codebase", 0.0, "done")
            except Exception:
                pass

    # Check active skills first
    try:
        sm = SkillManager()
        snap = engine.snapshot()
        active_skills = sm.match_metrics(snap)
        state.active_skills = active_skills
        for sk in active_skills:
            _emit(state, "Skill", f"trigger: {sk.get('name', sk.get('id', '?'))}",
                  f"skill:{sk.get('id', '?')}", 0.0, "done")
    except Exception:
        active_skills = []

    swarm = Swarm(engine)

    # Emit events for each agent as they run
    _emit(state, "Planner", "analyzing Φ(G) decomposition", "analyze_phi", 0.0, "working")
    planner_phi = engine.snapshot()
    p_before = planner_phi.get("phi", 0.0) if isinstance(planner_phi, dict) else planner_phi.phi

    result = swarm.solve(task)

    phi_after = result.get("end_phi", p_before)

    # Log per-agent results from the swarm
    for agent_name, agent_result in result.get("results", {}).items():
        if agent_name == "planner":
            findings = agent_result.get("findings", [])
            _emit(state, "Planner", findings[0][:40] if findings else "plan ready",
                  "analyze_phi", agent_result.get("phi_delta", 0.0), "done")
        elif agent_name == "refactor":
            action_text = agent_result.get("action", "refactoring")[:40]
            _emit(state, "Refactor", action_text, "remove_edge / extract_interface",
                  agent_result.get("phi_delta", 0.0), "done")
        elif agent_name == "quality":
            action_text = agent_result.get("action", "quality boost")[:40]
            _emit(state, "Quality", action_text, "add_type_hints / split_function",
                  agent_result.get("phi_delta", 0.0), "done")
        elif agent_name == "test":
            _emit(state, "Test", agent_result.get("action", "coverage check")[:40],
                  "run_tests / verify_behavior",
                  agent_result.get("phi_delta", 0.0), "done")
        elif agent_name == "skill":
            _emit(state, "Skill", agent_result.get("action", "skills loaded")[:40],
                  f"{agent_result.get('skill_count', 0)} skills active",
                  0.0, "done")
        elif agent_name == "build":
            _emit(state, "Build", agent_result.get("action", "validate")[:40],
                  "validate / check_tests", 0.0, "done")
        elif agent_name == "repo":
            _emit(state, "Repo", agent_result.get("action", "repo check")[:40],
                  "git_status", 0.0, "done")

    total_delta = phi_after - phi_before
    _emit(state, "Swarm", f"done · {len(result.get('agents_used', []))} agents · ΔΦ {total_delta:+.4f}",
          "", total_delta, "done")

    # Write a swarm report file if filetree is connected
    if state.filetree:
        report_content = result.get("report", "")
        if report_content:
            report_path = ".agent-storm/last-swarm-report.md"
            import time as _t
            header = f"# Swarm Report\n_Task: {task}_\n_Time: {_t.strftime('%Y-%m-%d %H:%M:%S')}_\n\n"
            state.filetree.write(report_path, header + report_content, agent="Swarm")
            _emit(state, "Swarm", f"wrote: {report_path}", "write_file", total_delta, "done")

    return result.get("report", "Swarm complete.")


# ── Smart built-in responses ──────────────────────────────────────────────────

def _smart_response(state: AppState, user_msg: str) -> str:
    """Built-in response using real Φ(G) math. No LLM required."""
    engine = state.engine
    msg_lower = user_msg.strip().lower()

    # /metrics
    if msg_lower in ("/metrics", "metrics", "phi") or msg_lower.startswith("/metrics"):
        m = engine.metrics
        if m is None:
            return "No metrics available. Engine not seeded."
        coeffs = Regime.coeffs(engine.current_regime)
        alpha_q  = coeffs.alpha  * m.q
        beta_c   = coeffs.beta   * m.coupling
        gamma_v  = coeffs.gamma  * m.mean_v
        return (
            f"Φ(G) = {m.phi:+.4f} [{engine.current_regime}]\n"
            f"\n"
            f"Objective: Φ(G) = α·Q − β·Č − γ·V\n"
            f"Coefficients: α={coeffs.alpha} β={coeffs.beta} γ={coeffs.gamma}\n"
            f"\n"
            f"α·Q    = {coeffs.alpha} × {m.q:.4f} = {alpha_q:+.4f}\n"
            f"-β·Č  = -{coeffs.beta} × {m.coupling:.4f} = {-beta_c:+.4f}\n"
            f"-γ·V  = -{coeffs.gamma} × {m.mean_v:.4f} = {-gamma_v:+.4f}\n"
            f"──────────────────────────────\n"
            f"Φ(G)   = {m.phi:+.4f}\n"
            f"\n"
            f"Graph: {m.n_nodes} nodes · {m.n_edges} edges · {m.n_modules} modules"
        )

    # /sweep
    if msg_lower in ("/sweep", "sweep") or msg_lower.startswith("/sweep"):
        sweep = engine.sweep_regimes()
        best_r, best_phi = max(sweep, key=lambda x: x[1])
        current_phi = engine.metrics.phi if engine.metrics else 0.0
        lines = ["Φ(G) Regime Sweep\n"]
        for r, phi in sweep:
            marker = " ← BEST" if r == best_r else ""
            active = " [current]" if r == engine.current_regime else ""
            delta = phi - current_phi
            delta_str = f"{delta:+.4f}" if r != engine.current_regime else ""
            lines.append(f"  {r.upper():10s}  Φ={phi:+.4f}{marker}{active}  {delta_str}")
        if best_r != engine.current_regime:
            improvement = best_phi - current_phi
            lines.append(f"\nSuggestion: /switch {best_r} (+{improvement:.4f} Φ improvement)")
        else:
            lines.append(f"\nCurrent regime '{engine.current_regime}' is already optimal.")
        return "\n".join(lines)

    # /theory
    if msg_lower in ("/theory", "theory") or msg_lower.startswith("/theory"):
        return engine.theory_explain()

    # /history
    if msg_lower in ("/history", "history") or msg_lower.startswith("/history"):
        if not engine.transitions:
            return "No regime transitions recorded yet.\nUse /switch <regime> to switch manually."
        lines = ["Regime Transition History\n"]
        for i, t in enumerate(engine.transitions, start=1):
            delta = t.improvement()
            lines.append(f"#{i:02d}  {t.from_} → {t.to}  Φ: {t.phi_before:+.4f} → {t.phi_after:+.4f} ({delta:+.4f})")
            lines.append(f"    {t.reason}")
        return "\n".join(lines)

    # /switch <regime>
    if msg_lower.startswith("/switch") or msg_lower.startswith("switch "):
        parts = user_msg.strip().split()
        target = parts[-1].lower() if len(parts) >= 2 else ""
        valid = Regime.from_str(target)
        if valid:
            old_phi = engine.metrics.phi if engine.metrics else 0.0
            engine.switch_regime(valid)
            new_phi = engine.metrics.phi if engine.metrics else 0.0
            delta = new_phi - old_phi
            return (
                f"Φ(G) = {new_phi:+.4f} [{valid}]\n"
                f"\n"
                f"Switched from {target} to {valid}.\n"
                f"Φ change: {delta:+.4f}\n"
                f"\n"
                f"Q={engine.metrics.q:.4f}  Č={engine.metrics.coupling:.4f}  V={engine.metrics.mean_v:.2f}"
            )
        else:
            return f"Unknown regime '{target}'. Valid: simple, advanced, hybrid.\nExample: /switch simple"

    # /simulate
    if msg_lower in ("/simulate", "simulate") or msg_lower.startswith("/simulate"):
        old_phi = engine.metrics.phi if engine.metrics else 0.0
        engine.simulate_deviation()
        new_phi = engine.metrics.phi if engine.metrics else 0.0
        delta = new_phi - old_phi
        direction = "improved" if delta > 0 else "degraded"
        return (
            f"Φ(G) = {new_phi:+.4f} [{engine.current_regime}]\n"
            f"\n"
            f"Simulation complete. Φ {direction} by {delta:+.4f}.\n"
            f"\n"
            f"Q={engine.metrics.q:.4f}  Č={engine.metrics.coupling:.4f}  V={engine.metrics.mean_v:.2f}\n"
            f"\n"
            f"Type /metrics for full breakdown."
        )

    # /connect <path>
    if msg_lower.startswith("/connect") or msg_lower.startswith("connect "):
        parts = user_msg.strip().split(maxsplit=1)
        path = parts[1].strip() if len(parts) > 1 else "~"
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        if not os.path.isdir(path):
            return f"Not a directory: {path}\n\nTry:\n  /connect ~\n  /connect ~/projects\n  /connect /sdcard"
        try:
            state.filetree = FileTree(path)
            n = len(state.filetree.files)
            summary = state.filetree.summary()
            state.file_selected = 0
            state.file_scroll = 0
            state.tree_scroll = 0
            _emit(state, "FileSystem", f"connected: {path}", "scan_dir", 0.0, "done")
            return (
                f"Connected to: {path}\n"
                f"{summary}\n"
                f"\n"
                f"Tab [6] → browse and view files\n"
                f"Commands:\n"
                f"  /ls           list files\n"
                f"  /read <file>  open a file\n"
                f"  /write <file> <content>  write a file\n"
                f"  /swarm <task> run agents on your code"
            )
        except Exception as e:
            return f"Connect failed: {e}"

    # /ls [path]
    if msg_lower in ("/ls", "ls") or msg_lower.startswith("/ls "):
        if state.filetree is None:
            return "No directory connected. Use /connect <path> first."
        parts = user_msg.strip().split(maxsplit=1)
        subpath = parts[1].strip() if len(parts) > 1 else ""
        entries = state.filetree.list_dir(subpath)
        if not entries:
            return f"Empty directory: {subpath or state.filetree.root}"
        lines = [f"Contents of {subpath or '/'}: ({len(entries)} items)\n"]
        for name, is_dir in entries[:40]:
            icon = "📁" if is_dir else "  "
            lines.append(f"  {icon} {name}")
        if len(entries) > 40:
            lines.append(f"  … {len(entries) - 40} more")
        return "\n".join(lines)

    # /read <file>
    if msg_lower.startswith("/read ") or msg_lower.startswith("read "):
        if state.filetree is None:
            return "No directory connected. Use /connect <path> first."
        parts = user_msg.strip().split(maxsplit=1)
        relpath = parts[1].strip() if len(parts) > 1 else ""
        if not relpath:
            return "Usage: /read <file>"
        content = state.filetree.read(relpath, agent="Chat")
        _emit(state, "FileSystem", f"read: {relpath}", "read_file",
              0.0, "done")
        state.tab = Tab.CODE  # auto-switch to code tab
        lines = content.splitlines()
        preview = "\n".join(lines[:20])
        suffix = f"\n… ({len(lines) - 20} more lines)" if len(lines) > 20 else ""
        return f"Opened: {relpath} ({len(lines)} lines)\nTab [6] → full view\n\n```\n{preview}{suffix}\n```"

    # /write <file>
    if msg_lower.startswith("/write "):
        if state.filetree is None:
            return "No directory connected. Use /connect <path> first."
        parts = user_msg.strip().split(maxsplit=2)
        if len(parts) < 3:
            return "Usage: /write <file> <content>"
        relpath = parts[1].strip()
        content = parts[2]
        ok = state.filetree.write(relpath, content, agent="Chat")
        if ok:
            _emit(state, "FileSystem", f"wrote: {relpath}", "write_file", 0.0, "done")
            state.tab = Tab.CODE
            return f"Written: {relpath} ({content.count(chr(10)) + 1} lines)\nTab [6] → view file"
        return f"Write failed: {relpath}"

    # /skills
    if msg_lower in ("/skills", "skills") or msg_lower.startswith("/skills"):
        try:
            from .skills import SkillManager
            sm = SkillManager()
            snap = engine.snapshot()
            active = sm.match_metrics(snap)
            state.active_skills = active
            active_ids = {s.get("id") for s in active}
            lines = ["Skills (★ = triggered by current metrics):\n"]
            for sk in sm._yaml_skills:
                marker = "★ ACTIVE" if sk.get("id") in active_ids else "  ·    "
                lines.append(f"  {marker}  [{sk.get('id')}] {sk.get('name', '')}")
                lines.append(f"            {sk.get('description', '')}")
                if sk.get("id") in active_ids and sk.get("action"):
                    lines.append(f"            → {sk['action'][:100].strip()}")
            for sk in sm.skills.values():
                lines.append(f"  ·       [{sk.category}] {sk.name}: {sk.description[:60]}")
            if not sm._yaml_skills and not sm.skills:
                lines.append("  No skills loaded.")
            lines.append("\nSee tab [5] for live agent activity.")
            return "\n".join(lines)
        except Exception as e:
            return f"Skills error: {e}"

    # /swarm <task>
    if msg_lower.startswith("/swarm") or msg_lower.startswith("swarm "):
        task = user_msg.strip()
        for prefix in ("/swarm ", "swarm "):
            if task.lower().startswith(prefix):
                task = task[len(prefix):]
                break
        if not task or task.lower() in ("swarm", "/swarm"):
            task = "optimize Φ(G) — reduce coupling and complexity"
        return _run_swarm(state, task)

    # /help
    if msg_lower in ("/help", "help", "?") or msg_lower.startswith("/help"):
        return (
            "Available commands:\n"
            "\n"
            "  /metrics   Live Φ(G) breakdown\n"
            "  /sweep     Compare all regimes\n"
            "  /theory    Full mathematical explanation\n"
            "  /history   Regime transition log\n"
            "  /switch <r>  Switch regime (simple/advanced/hybrid)\n"
            "  /simulate  Run graph deviation step\n"
            "  /skills    Show all skills + which are active\n"
            "  /swarm <task>  Run 8-agent swarm on a task\n"
            "  /help      Show this help\n"
            "\n"
            "Or just type any message for automatic Φ(G) analysis.\n"
            "Tab [5] shows live agent activity and active skills."
        )

    # ── General fallback: full Φ(G) analysis ──────────────────────────────────
    engine.update_metrics()
    m = engine.metrics
    if m is None:
        return "Engine not ready. Call seed_graph() first."

    coeffs = Regime.coeffs(engine.current_regime)
    alpha_q  = coeffs.alpha  * m.q
    beta_c   = coeffs.beta   * m.coupling
    gamma_v  = coeffs.gamma  * m.mean_v

    # Find dominant issue (most negative contribution)
    terms = [
        ("α·Q",   alpha_q,  "modularity is low (few intra-module connections)"),
        ("-β·Č", -beta_c,  "coupling is high (cross-module edges)"),
        ("-γ·V", -gamma_v, "complexity is high (cyclomatic violations)"),
    ]
    terms.sort(key=lambda x: x[1])
    worst_name, worst_val, worst_reason = terms[0]

    lines = [
        f"Φ(G) = {m.phi:+.4f} [{engine.current_regime}]",
        f"Q={m.q:.4f}  Č={m.coupling:.4f}  V={m.mean_v:.2f}",
        "",
        f"Dominant issue: {worst_name}({worst_reason[:40]}..)" if len(worst_reason) > 40 else f"Dominant issue: {worst_name} — {worst_reason}",
    ]

    # Which term is largest negative?
    if worst_name == "-β·Č":
        lines.append(f"  Term: -β·Č = -{coeffs.beta} × {m.coupling:.3f} = {-beta_c:+.3f}")
    elif worst_name == "-γ·V":
        lines.append(f"  Term: -γ·V = -{coeffs.gamma} × {m.mean_v:.3f} = {-gamma_v:+.3f}")
    else:
        lines.append(f"  Term: α·Q = {coeffs.alpha} × {m.q:.3f} = {alpha_q:+.3f}")

    lines.append("")
    lines.append(f"Graph: {m.n_nodes} nodes · {m.n_edges} edges · {m.n_modules} modules")

    # Sweep and suggest
    sweep = engine.sweep_regimes()
    best_r, best_phi = max(sweep, key=lambda x: x[1])
    improvement = best_phi - m.phi
    if best_r != engine.current_regime and improvement > 0.01:
        lines.append(f"Suggestion: /switch {best_r} (+{improvement:.2f} Φ improvement)")

    lines.append("")
    lines.append("Type /help for all commands.")

    return "\n".join(lines)


# ── Input processing ──────────────────────────────────────────────────────────

def _process_input(state: AppState, user_msg: str) -> None:
    """Process user input: append to messages, get response, update metrics."""
    if not user_msg.strip():
        return

    # Append user message
    state.messages.append(Message(Role.USER, user_msg))

    # Always refresh active skills before processing
    try:
        from .skills import SkillManager
        sm = SkillManager()
        snap = state.engine.snapshot()
        state.active_skills = sm.match_metrics(snap)
        for sk in state.active_skills:
            _emit(state, "Skill", f"monitoring: {sk.get('name', sk.get('id', '?'))}",
                  f"skill:{sk.get('id', '?')}", 0.0, "done")
    except Exception:
        pass

    response = None
    phi_before = state.engine.metrics.phi if state.engine.metrics else 0.0

    _emit(state, "Chat", f"processing: {user_msg[:35]}", "NeuralAgent", 0.0, "working")

    # Try NeuralAgent if available (lazy init)
    if state._agent is None:
        try:
            from .chat import NeuralAgent
            state._agent = NeuralAgent(state.engine)
        except Exception:
            state._agent = False  # mark as unavailable

    if state._agent and state._agent is not False:
        try:
            response = state._agent.chat(user_msg)
            _emit(state, "Chat", "response ready", "NeuralAgent + Φ(G)", 0.0, "done")
        except Exception:
            response = None

    if response is None:
        response = _smart_response(state, user_msg)
        if response:
            _emit(state, "Chat", "smart response (no LLM)", "Φ(G) analysis", 0.0, "done")

    # Get current phi for agent message
    state.engine.update_metrics()
    phi_now = state.engine.metrics.phi if state.engine.metrics else None
    phi_delta = (phi_now - phi_before) if phi_now is not None else 0.0
    if phi_delta != 0.0:
        _emit(state, "System", f"Φ(G) changed", "metrics_update", phi_delta, "done")

    state.messages.append(Message(Role.AGENT, response, phi=phi_now))
    state.engine.update_metrics()
    state.chat_scroll = 0  # scroll to bottom


# ── Initial messages ──────────────────────────────────────────────────────────

def _initial_messages(engine: RegimeEngine) -> List[Message]:
    """Return initial SYSTEM message."""
    m = engine.metrics
    phi = m.phi if m else 0.0
    regime = engine.current_regime.upper()

    text = (
        f"Deep Agent Storm Swarm · 8-agent swarm online\n"
        f"Φ(G) = {phi:+.4f} · regime: {regime}\n"
        f"─────────────────────────────────────────────\n"
        f"  /connect ~        connect to your files\n"
        f"  /swarm <task>     run 8-agent swarm\n"
        f"  /skills  /metrics  /sweep  /help\n"
        f"Tab [5] agents · [6] code viewer"
    )
    return [Message(Role.SYSTEM, text)]


# ── Main loop ─────────────────────────────────────────────────────────────────

def _main(stdscr) -> None:
    """Main curses event loop."""
    _setup_colors(stdscr)
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    # Create engine and seed
    engine = RegimeEngine()
    engine.seed_graph()

    # Create app state
    state = AppState(
        engine=engine,
        messages=_initial_messages(engine),
    )

    last_refresh = time.time()
    REFRESH_INTERVAL = 5.0

    while True:
        # Auto-refresh metrics every 5 seconds
        now = time.time()
        if now - last_refresh >= REFRESH_INTERVAL:
            try:
                state.engine.update_metrics()
            except Exception:
                pass
            last_refresh = now

        # Render
        try:
            render(stdscr, state)
        except curses.error:
            pass

        # Non-blocking key read
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key == -1:
            time.sleep(0.05)
            continue

        # Help overlay: any key closes it
        if state.show_help:
            state.show_help = False
            continue

        # ── Tab switches ──────────────────────────────────────────────────────
        if key == ord('1'):
            state.tab = Tab.CHAT
            continue
        if key == ord('2'):
            state.tab = Tab.METRICS
            continue
        if key == ord('3'):
            state.tab = Tab.THEORY
            continue
        if key == ord('4'):
            state.tab = Tab.HISTORY
            continue
        if key == ord('5'):
            state.tab = Tab.AGENTS
            continue
        if key == ord('6'):
            state.tab = Tab.CODE
            continue

        # ── Refresh ───────────────────────────────────────────────────────────
        if key == ord('r'):
            try:
                state.engine.update_metrics()
            except Exception:
                pass
            last_refresh = time.time()
            continue

        # ── Help toggle ───────────────────────────────────────────────────────
        if key == ord('?'):
            state.show_help = True
            continue

        # ── Quit (only if input buffer empty) ─────────────────────────────────
        if key == ord('q') and not state.input_buf:
            break

        # ── Scroll / navigation ───────────────────────────────────────────────
        if state.tab == Tab.CODE and state.filetree:
            ft = state.filetree
            n_files = len(ft.files)
            if key == curses.KEY_UP:
                state.file_selected = max(0, state.file_selected - 1)
                if state.file_selected < state.tree_scroll:
                    state.tree_scroll = state.file_selected
                continue
            if key == curses.KEY_DOWN:
                state.file_selected = min(n_files - 1, state.file_selected + 1)
                h2, _ = stdscr.getmaxyx()
                tree_visible = h2 - 4 - 1
                if state.file_selected >= state.tree_scroll + tree_visible:
                    state.tree_scroll = state.file_selected - tree_visible + 1
                continue
            if key == curses.KEY_PPAGE:
                state.file_scroll = max(0, state.file_scroll - 20)
                continue
            if key == curses.KEY_NPAGE:
                state.file_scroll += 20
                continue
            if key in (curses.KEY_ENTER, ord('\r'), ord('\n'), 10, 13):
                if 0 <= state.file_selected < n_files and not state.input_buf:
                    relpath = ft.files[state.file_selected]
                    ft.read(relpath, agent="FileSystem")
                    state.file_scroll = 0
                    _emit(state, "FileSystem", f"opened: {relpath}", "read_file", 0.0, "done")
                    continue
        if key == curses.KEY_UP:
            state.chat_scroll += 1
            continue
        if key == curses.KEY_DOWN:
            state.chat_scroll = max(0, state.chat_scroll - 1)
            continue
        if key == curses.KEY_PPAGE:   # Page Up
            state.chat_scroll += 10
            continue
        if key == curses.KEY_NPAGE:   # Page Down
            state.chat_scroll = max(0, state.chat_scroll - 10)
            continue

        # ── Terminal resize ────────────────────────────────────────────────────
        if key == curses.KEY_RESIZE:
            stdscr.clear()
            continue

        # ── Escape: clear input ────────────────────────────────────────────────
        if key == 27:
            state.input_buf = ""
            state.error = None
            continue

        # ── Enter: process input ───────────────────────────────────────────────
        if key in (curses.KEY_ENTER, ord('\r'), ord('\n'), 10, 13):
            buf = state.input_buf.strip()
            state.input_buf = ""
            state.error = None
            if buf:
                try:
                    _process_input(state, buf)
                except Exception as exc:
                    state.error = str(exc)[:60]
                    state.messages.append(Message(Role.SYSTEM, f"Error: {exc}"))
            continue

        # ── Backspace ─────────────────────────────────────────────────────────
        if key in (curses.KEY_BACKSPACE, 127, 8):
            if state.input_buf:
                state.input_buf = state.input_buf[:-1]
            continue

        # ── Printable ASCII ───────────────────────────────────────────────────
        if 32 <= key <= 126:
            state.input_buf += chr(key)
            continue


# ── Entry points ──────────────────────────────────────────────────────────────

def run_tui() -> None:
    """Launch the TUI via curses.wrapper."""
    curses.wrapper(_main)


if __name__ == "__main__":
    run_tui()
