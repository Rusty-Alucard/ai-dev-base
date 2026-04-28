#!/usr/bin/env python3
"""
claude-usage.py — Claude Code transcript analyzer.

Parses ~/.claude/projects/{PROJECT}/*.jsonl and generates usage reports.

Usage:
  python bin/claude-usage.py [--range {7d|iso-week}] [--output logs/claude-usage/] [--project PATH]
  python bin/claude-usage.py --period 7d  # backward compat alias for --range 7d
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("ERROR: matplotlib is required. Install: pip install matplotlib", file=sys.stderr)
    sys.exit(1)


# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG_PATH = Path("config/claude-usage.yaml")


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    if not HAS_YAML:
        print(
            f"Warning: PyYAML not installed; config file {config_path} ignored, "
            "using built-in defaults. Install with: pip install pyyaml",
            file=sys.stderr,
        )
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_period(period_str: str) -> int:
    m = re.match(r"^(\d+)d?$", period_str)
    if not m:
        raise ValueError(f"Invalid period: {period_str!r}. Use e.g. '7d' or '30'")
    return int(m.group(1))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Analyze Claude Code transcript usage")
    p.add_argument(
        "--period",
        default=None,
        help="Analysis period (e.g. '7d', '30d') — kept for backward compat, same as --range 7d",
    )
    p.add_argument(
        "--range",
        dest="range_mode",
        default="7d",
        choices=["7d", "iso-week"],
        help="Analysis range: '7d' (last 7 days, default) or 'iso-week' (current ISO week Mon–Sun)",
    )
    p.add_argument("--output", default="logs/claude-usage/", help="Output directory")
    p.add_argument("--project", default=None, help="Claude project JSONL directory (or set CLAUDE_PROJECT_PATH)")
    p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Config YAML path")
    return p


def resolve_date_range(args, config: dict, now: datetime = None) -> tuple:
    """Returns (since_utc, date_range_list, period_label)."""
    if now is None:
        now = datetime.now(UTC)
    today = now.date()

    # --period takes precedence over --range for backward compat
    if args.period is not None:
        days = parse_period(args.period)
        since = now - timedelta(days=days)
        date_range = [(since + timedelta(days=i)).date() for i in range(days + 1)]
        return since, date_range, f"{days}d"

    if args.range_mode == "iso-week":
        weekday = today.weekday()  # 0=Mon, 6=Sun
        start = today - timedelta(days=weekday)
        end = min(today, start + timedelta(days=6))
        since = datetime(start.year, start.month, start.day, tzinfo=UTC)
        date_range = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        iso_week = today.isocalendar()[1]
        return since, date_range, f"W{iso_week:02d}"

    # default: 7d sliding window
    days = 7
    since = now - timedelta(days=days)
    date_range = [(since + timedelta(days=i)).date() for i in range(days + 1)]
    return since, date_range, "7d"


# ── JSONL Parsing ─────────────────────────────────────────────────────────────


def model_family(model_name: str) -> str:
    name = (model_name or "").lower()
    if "opus" in name:
        return "Opus"
    if "sonnet" in name:
        return "Sonnet"
    if "haiku" in name:
        return "Haiku"
    return "Other"


_CLEAR_RE = re.compile(r"<command-name>/clear</command-name>")


def scan_jsonl(project_path: Path, since: datetime) -> dict:
    stats = {
        "agent_spawns": defaultdict(int),
        "model_tokens": defaultdict(lambda: defaultdict(int)),  # date -> family -> output tokens
        "model_input_tokens": defaultdict(lambda: defaultdict(int)),  # date -> family -> input tokens
        "daily_tools": defaultdict(int),
        "daily_sessions": defaultdict(set),
        "mcp_usage": defaultdict(int),
        "skill_usage": defaultdict(int),
        "sessions_with_skills": set(),  # session_ids that had at least one Skill tool_use
        "tool_type_usage": defaultdict(int),  # tool name (mcp__* grouped as "MCP") -> count
        "daily_clears": defaultdict(int),  # date -> /clear invocation count
    }

    jsonl_files = sorted(project_path.glob("*.jsonl"))
    if not jsonl_files:
        print(f"Warning: no JSONL files in {project_path}", file=sys.stderr)
        return stats

    for fpath in jsonl_files:
        try:
            _parse_file(fpath, since, stats)
        except Exception as e:
            print(f"Warning: skipping {fpath.name}: {e}", file=sys.stderr)

    return stats


def _parse_file(fpath: Path, since: datetime, stats: dict) -> None:
    with open(fpath, encoding="utf-8", errors="replace") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type")
            if entry_type not in ("assistant", "user"):
                continue

            ts_str = entry.get("timestamp", "")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except ValueError:
                continue

            if ts < since:
                continue

            date_key = ts.date().isoformat()

            if entry_type == "user":
                content = entry.get("message", {}).get("content", "")
                if isinstance(content, str) and _CLEAR_RE.search(content):
                    stats["daily_clears"][date_key] += 1
                continue

            # assistant entries
            session_id = entry.get("sessionId", "")
            msg = entry.get("message", {})

            if session_id:
                stats["daily_sessions"][date_key].add(session_id)

            usage = msg.get("usage", {})
            output_tokens = usage.get("output_tokens", 0)
            input_tokens = usage.get("input_tokens", 0)
            # cache_creation_input_tokens / cache_read_input_tokens have different pricing;
            # included in input_tokens sum for simplicity. Separate cache pricing TBD.

            if output_tokens or input_tokens:
                family = model_family(msg.get("model", ""))
                if output_tokens:
                    stats["model_tokens"][date_key][family] += output_tokens
                if input_tokens:
                    stats["model_input_tokens"][date_key][family] += input_tokens

            for item in msg.get("content", []):
                if item.get("type") != "tool_use":
                    continue
                tool_name = item.get("name", "")
                stats["daily_tools"][date_key] += 1

                # Group mcp__* calls as "MCP" for tool type chart
                tool_type = "MCP" if tool_name.startswith("mcp__") else tool_name
                stats["tool_type_usage"][tool_type] += 1

                if tool_name == "Agent":
                    subtype = item.get("input", {}).get("subagent_type", "general-purpose")
                    stats["agent_spawns"][subtype] += 1

                if tool_name == "Skill":
                    skill_name = item.get("input", {}).get("skill", "(unknown)")
                    stats["skill_usage"][skill_name] += 1
                    if session_id:
                        stats["sessions_with_skills"].add(session_id)

                if tool_name.startswith("mcp__"):
                    parts = tool_name.split("__")
                    service = parts[1] if len(parts) > 1 else tool_name
                    stats["mcp_usage"][service] += 1


# ── Learnings Parser ─────────────────────────────────────────────────────────

_TAG_RE = re.compile(r"#[a-z][a-z0-9-]*")
_LEARNINGS_SECTION_RE = re.compile(r"^##\s+Learnings\b", re.MULTILINE)
_NEXT_SECTION_RE = re.compile(r"^##\s+", re.MULTILINE)


def parse_learnings(agents_dir: Path) -> dict:
    """Parse Learnings sections from .claude/agents/*.md files.

    Args:
        agents_dir: Path to the directory containing agent persona .md files.

    Returns:
        Dict with keys:
          - "by_persona": {persona_name: {"entries": int, "tags": Counter}}
          - "global_tags": Counter of all tags across all personas
          - "total_entries": int
    """
    by_persona: dict[str, dict] = {}
    global_tags: Counter = Counter()
    total_entries = 0

    for md_path in sorted(agents_dir.glob("*.md")):
        persona = md_path.stem
        text = md_path.read_text(encoding="utf-8", errors="replace")

        # Find the ## Learnings section
        m = _LEARNINGS_SECTION_RE.search(text)
        if not m:
            continue

        section_start = m.end()
        # Find the next ## section (if any) to delimit the Learnings block
        next_section = _NEXT_SECTION_RE.search(text, section_start)
        section_text = text[section_start : next_section.start() if next_section else len(text)]

        persona_tags: Counter = Counter()
        entry_count = 0

        for line in section_text.splitlines():
            stripped = line.strip()
            # Count bullet-list entries (- **...** or - plain text)
            if stripped.startswith("- ") and len(stripped) > 2:
                entry_count += 1
                tags = _TAG_RE.findall(stripped)
                persona_tags.update(tags)
                global_tags.update(tags)

        if entry_count > 0:
            by_persona[persona] = {
                "entries": entry_count,
                "tags": persona_tags,
            }
            total_entries += entry_count

    return {
        "by_persona": by_persona,
        "global_tags": global_tags,
        "total_entries": total_entries,
    }


def load_learnings_config(config: dict) -> dict:
    """Extract learnings config section with defaults.

    Args:
        config: Full config dict loaded from YAML.

    Returns:
        Learnings config dict with keys: enabled, root, promotion_threshold.
    """
    raw = config.get("learnings", {})
    return {
        "enabled": raw.get("enabled", True),
        "root": raw.get("root", ".claude/agents"),
        "promotion_threshold": int(raw.get("promotion_threshold", 3)),
    }


def build_learnings_report_section(learnings_data: dict, promotion_threshold: int = 3) -> list[str]:
    """Build the markdown lines for Section 7: Learnings.

    Args:
        learnings_data: Output from parse_learnings().
        promotion_threshold: Minimum tag count to appear in promotion candidates.

    Returns:
        List of markdown lines.
    """
    global_tags: Counter = learnings_data["global_tags"]
    by_persona: dict = learnings_data["by_persona"]
    total_entries: int = learnings_data["total_entries"]
    total_tags = sum(global_tags.values())
    unique_tags = len(global_tags)

    lines = [
        "## 7. Learnings (Harness Gardening)",
        "",
        "### Tag frequency (top 10)",
        "",
    ]

    top_tags = global_tags.most_common(10)
    if top_tags:
        lines += ["| Rank | Tag | Count |", "|---|---|---|"]
        for rank, (tag, count) in enumerate(top_tags, 1):
            lines.append(f"| {rank} | {tag} | {count} |")
        lines.append("")
    else:
        lines += ["(no tags found)", ""]

    lines += [
        "### Persona breakdown",
        "",
        "| Persona | Entries | Unique tags |",
        "|---|---|---|",
    ]
    for persona in sorted(by_persona.keys()):
        data = by_persona[persona]
        lines.append(f"| {persona} | {data['entries']} | {len(data['tags'])} |")

    if not by_persona:
        lines.append("| (no data) | 0 | 0 |")

    lines.append("")

    # 3-strike promotion candidates
    candidates = [(tag, count) for tag, count in global_tags.most_common() if count >= promotion_threshold]
    lines += [f"### Promotion candidates ({promotion_threshold}+ occurrences)", ""]
    if candidates:
        for tag, count in candidates:
            lines.append(f"- {tag} ({count} occurrences)")
    else:
        lines.append("(none)")
    lines.append("")

    lines.append(f"Total entries: {total_entries} / Total tags: {total_tags} / Unique tags: {unique_tags}")
    lines.append("")

    return lines


# ── Cost Calculation ──────────────────────────────────────────────────────────

_DEFAULT_PRICING = {
    "Opus": {"input": 15.0, "output": 75.0},
    "Sonnet": {"input": 3.0, "output": 15.0},
    "Haiku": {"input": 0.8, "output": 4.0},
}


def load_pricing(config: dict) -> dict:
    """Returns {Family: {input: $/1M tokens, output: $/1M tokens}}."""
    raw = config.get("pricing", {})
    if not raw:
        return _DEFAULT_PRICING
    pricing = {}
    for key, rates in raw.items():
        family = key.capitalize()
        pricing[family] = {"input": float(rates.get("input", 0.0)), "output": float(rates.get("output", 0.0))}
    return pricing


def compute_daily_cost(stats: dict, pricing: dict) -> dict:
    """Returns {date_str: {family: cost_usd}}."""
    daily_cost: dict = defaultdict(lambda: defaultdict(float))
    all_dates = set(stats["model_tokens"].keys()) | set(stats["model_input_tokens"].keys())
    for date_key in all_dates:
        for family, rates in pricing.items():
            in_tok = stats["model_input_tokens"][date_key].get(family, 0)
            out_tok = stats["model_tokens"][date_key].get(family, 0)
            cost = (in_tok * rates["input"] + out_tok * rates["output"]) / 1_000_000
            if cost > 0:
                daily_cost[date_key][family] = cost
    return daily_cost


# ── Plotting ──────────────────────────────────────────────────────────────────

_FAMILY_COLORS = {
    "Opus": "#7c3aed",
    "Sonnet": "#2563eb",
    "Haiku": "#059669",
    "Other": "#94a3b8",
}
_BAR_BLUE = "#3b82f6"
_BAR_GREEN = "#059669"
_BAR_PURPLE = "#7c3aed"
_BAR_ORANGE = "#f59e0b"


def _save(fig: "plt.Figure", path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")
    return path


def _barh_chart(ax, items: list, color: str) -> None:
    labels, values = zip(*items, strict=False)
    y = list(range(len(labels)))
    bars = ax.barh(y, list(values), color=color, edgecolor="white")
    ax.set_yticks(y)
    ax.set_yticklabels(list(labels))
    ax.invert_yaxis()
    for bar, val in zip(bars, values, strict=False):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2, str(val), va="center", fontsize=9)


def plot_skill_usage(stats: dict, images_dir: Path) -> Path:
    skills = dict(stats["skill_usage"]) or {"(no data)": 0}
    items = sorted(skills.items(), key=lambda x: x[1], reverse=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(items) * 0.5)))
    _barh_chart(ax, items, _BAR_PURPLE)
    ax.set_xlabel("Invocation count")
    ax.set_title("Skill Usage (by skill name)")
    fig.tight_layout()
    return _save(fig, images_dir / "skill_usage.png")


def plot_agent_spawn_frequency(stats: dict, images_dir: Path) -> Path:
    spawns = dict(stats["agent_spawns"]) or {"(no data)": 0}
    items = sorted(spawns.items(), key=lambda x: x[1], reverse=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(items) * 0.5)))
    _barh_chart(ax, items, _BAR_BLUE)
    ax.set_xlabel("Spawn count")
    ax.set_title("Agent Spawn Frequency (by subagent_type)")
    fig.tight_layout()
    return _save(fig, images_dir / "agent_spawn_frequency.png")


def plot_mcp_usage(stats: dict, images_dir: Path) -> Path:
    mcp = dict(stats["mcp_usage"]) or {"(no data)": 0}
    items = sorted(mcp.items(), key=lambda x: x[1], reverse=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(items) * 0.5)))
    _barh_chart(ax, items, _BAR_GREEN)
    ax.set_xlabel("Usage count")
    ax.set_title("MCP Tool Usage (by service)")
    fig.tight_layout()
    return _save(fig, images_dir / "mcp_usage.png")


def plot_tool_type_usage(stats: dict, images_dir: Path) -> Path:
    tools = dict(stats["tool_type_usage"]) or {"(no data)": 0}
    items = sorted(tools.items(), key=lambda x: x[1], reverse=True)

    fig, ax = plt.subplots(figsize=(10, max(4, len(items) * 0.5)))
    _barh_chart(ax, items, _BAR_ORANGE)
    ax.set_xlabel("Call count")
    ax.set_title("Tool Type Usage (by tool name)")
    fig.tight_layout()
    return _save(fig, images_dir / "tool_type_usage.png")


def plot_cost_daily(daily_cost: dict, images_dir: Path, date_range: list) -> Path:
    families = ["Opus", "Sonnet", "Haiku", "Other"]
    dates = [d.isoformat() for d in date_range]

    fig, ax = plt.subplots(figsize=(12, 5))
    bottom = [0.0] * len(dates)
    any_data = False
    for family in families:
        values = [daily_cost.get(d, {}).get(family, 0.0) for d in dates]
        if any(v > 0 for v in values):
            any_data = True
            ax.bar(
                dates,
                values,
                bottom=bottom,
                label=family,
                color=_FAMILY_COLORS.get(family, "#94a3b8"),
                edgecolor="white",
            )
            bottom = [b + v for b, v in zip(bottom, values, strict=False)]

    if not any_data:
        ax.text(0.5, 0.5, "(no data — add pricing to config)", ha="center", va="center", transform=ax.transAxes)

    ax.set_xlabel("Date")
    ax.set_ylabel("Cost (USD)")
    ax.set_title("Daily Cost (USD, by model family)")
    if any_data:
        ax.legend(loc="upper left")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return _save(fig, images_dir / "cost_daily.png")


def plot_model_token_consumption(stats: dict, images_dir: Path, date_range: list) -> Path:
    model_data = stats["model_tokens"]
    families = ["Opus", "Sonnet", "Haiku", "Other"]
    dates = [d.isoformat() for d in date_range]

    fig, ax = plt.subplots(figsize=(12, 5))
    bottom = [0] * len(dates)
    any_data = False
    for family in families:
        values = [model_data.get(d, {}).get(family, 0) for d in dates]
        if any(v > 0 for v in values):
            any_data = True
            ax.bar(
                dates,
                values,
                bottom=bottom,
                label=family,
                color=_FAMILY_COLORS.get(family, "#94a3b8"),
                edgecolor="white",
            )
            bottom = [b + v for b, v in zip(bottom, values, strict=False)]

    if not any_data:
        ax.text(0.5, 0.5, "(no data)", ha="center", va="center", transform=ax.transAxes)

    ax.set_xlabel("Date")
    ax.set_ylabel("Output tokens")
    ax.set_title("Model Token Consumption (daily, by family)")
    if any_data:
        ax.legend(loc="upper left")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return _save(fig, images_dir / "model_token_consumption.png")


def plot_daily_activity(stats: dict, images_dir: Path, date_range: list) -> Path:
    dates_str = [d.isoformat() for d in date_range]
    tool_counts = [stats["daily_tools"].get(d, 0) for d in dates_str]
    session_counts = [len(stats["daily_sessions"].get(d, set())) for d in dates_str]

    fig, ax1 = plt.subplots(figsize=(12, 5))
    c_tools = "#2563eb"
    c_sess = "#f59e0b"

    ax1.plot(dates_str, tool_counts, color=c_tools, marker="o", label="Tool calls", linewidth=2)
    ax1.set_ylabel("Tool call count", color=c_tools)
    ax1.tick_params(axis="y", labelcolor=c_tools)
    ax1.tick_params(axis="x", rotation=45)

    ax2 = ax1.twinx()
    ax2.plot(dates_str, session_counts, color=c_sess, marker="s", linestyle="--", label="Sessions", linewidth=2)
    ax2.set_ylabel("Session count", color=c_sess)
    ax2.tick_params(axis="y", labelcolor=c_sess)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    ax1.set_title("Daily Activity (tool calls & sessions)")
    fig.tight_layout()
    return _save(fig, images_dir / "daily_activity.png")


# ── Markdown Report ───────────────────────────────────────────────────────────


def _ranking_table(header_cols: list, rows: list) -> list:
    if not rows:
        return ["(no data)", ""]
    lines = ["| " + " | ".join(header_cols) + " |", "|" + "|".join(["---"] * len(header_cols)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return lines + [""]


def generate_report(
    stats: dict,
    period_label: str,
    date_range: list,
    output_path: Path,
    pricing: dict,
    learnings_data: dict | None = None,
    learnings_config: dict | None = None,
) -> None:
    """Generate the weekly markdown report.

    Args:
        stats: Aggregated usage stats from scan_jsonl().
        period_label: Human-readable period label (e.g. "7d", "W17").
        date_range: List of date objects covering the period.
        output_path: Path to write the output markdown file.
        pricing: Pricing config dict from load_pricing().
        learnings_data: Optional output from parse_learnings(). If None, section 7 is omitted.
        learnings_config: Optional learnings config from load_learnings_config().
    """
    dates_str = [d.isoformat() for d in date_range]
    total_tools = sum(stats["daily_tools"].values())
    total_sessions = sum(len(v) for v in stats["daily_sessions"].values())

    token_totals: dict = defaultdict(int)
    for day_data in stats["model_tokens"].values():
        for family, tokens in day_data.items():
            token_totals[family] += tokens
    total_tokens = sum(token_totals.values())

    total_skills = sum(stats["skill_usage"].values())
    total_spawns = sum(stats["agent_spawns"].values())
    total_mcp = sum(stats["mcp_usage"].values())
    total_tool_types = sum(stats["tool_type_usage"].values())
    total_clears = sum(stats["daily_clears"].values())

    daily_cost = compute_daily_cost(stats, pricing)
    total_cost = sum(sum(v.values()) for v in daily_cost.values())

    top_skills = sorted(stats["skill_usage"].items(), key=lambda x: x[1], reverse=True)[:5]
    top_agents = sorted(stats["agent_spawns"].items(), key=lambda x: x[1], reverse=True)[:5]
    top_mcp = sorted(stats["mcp_usage"].items(), key=lambda x: x[1], reverse=True)[:5]
    top_tools = sorted(stats["tool_type_usage"].items(), key=lambda x: x[1], reverse=True)[:10]

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    start_date = dates_str[0] if dates_str else "N/A"
    end_date = dates_str[-1] if dates_str else "N/A"

    cost_str = f"${total_cost:.4f}" if total_cost > 0 else "(no pricing config)"

    # Skill activation rate: count of unique sessions that invoked at least one Skill tool.
    sessions_with_skill = len(stats["sessions_with_skills"])
    activation_rate_pct = (sessions_with_skill / total_sessions * 100) if total_sessions > 0 else 0.0

    lines = [
        f"# Claude Code Usage Report — {period_label} ({start_date} to {end_date})",
        "",
        f"Generated: {now_str}",
        "",
        "## 1. Skills",
        "",
        f"Total skill invocations: **{total_skills:,}**",
        "",
    ]
    lines += _ranking_table(
        ["Rank", "Skill", "Count"],
        [(i, name, cnt) for i, (name, cnt) in enumerate(top_skills, 1)],
    )
    lines += [
        f"- Total sessions: {total_sessions}",
        f"- Sessions with ≥1 skill call: {sessions_with_skill} ({activation_rate_pct:.1f}%)",
        f"- Skill activation rate: {sessions_with_skill}/{total_sessions} = {activation_rate_pct:.1f}%",
        "",
        "![skill_usage.png](images/skill_usage.png)",
        "",
    ]

    lines += [
        "## 2. Subagent",
        "",
        f"Total agent spawns: **{total_spawns:,}**",
        "",
    ]
    lines += _ranking_table(
        ["Rank", "Agent Type", "Spawns"],
        [(i, name, cnt) for i, (name, cnt) in enumerate(top_agents, 1)],
    )
    lines += ["![agent_spawn_frequency.png](images/agent_spawn_frequency.png)", ""]

    lines += [
        "## 3. MCP",
        "",
        f"Total MCP calls: **{total_mcp:,}**",
        "",
    ]
    lines += _ranking_table(
        ["Rank", "Service", "Calls"],
        [(i, name, cnt) for i, (name, cnt) in enumerate(top_mcp, 1)],
    )
    lines += ["![mcp_usage.png](images/mcp_usage.png)", ""]

    lines += [
        "## 4. Tool Type",
        "",
        f"Total tool calls: **{total_tool_types:,}**",
        "",
    ]
    lines += _ranking_table(
        ["Rank", "Tool", "Count"],
        [(i, name, cnt) for i, (name, cnt) in enumerate(top_tools, 1)],
    )
    lines += ["![tool_type_usage.png](images/tool_type_usage.png)", ""]

    lines += [
        "## 5. CTX / Cost",
        "",
        f"Total estimated cost: **{cost_str}**",
        f"/clear invocations: **{total_clears}**",
        "",
        "### Daily Cost (USD)",
        "",
    ]
    cost_rows = [(d, sum(daily_cost.get(d, {}).values())) for d in dates_str if sum(daily_cost.get(d, {}).values()) > 0]
    if cost_rows:
        lines += ["| Date | Cost |", "|------|------|"]
        for date_d, cost_d in cost_rows:
            lines.append(f"| {date_d} | ${cost_d:.4f} |")
        lines.append("")
    else:
        lines += ["(no cost data — add pricing section to config/claude-usage.yaml)", ""]
    lines += ["![cost_daily.png](images/cost_daily.png)", ""]

    lines += [
        "## 6. Sum",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Period | {period_label} ({start_date} → {end_date}) |",
        f"| Total tool calls | {total_tools:,} |",
        f"| Total sessions | {total_sessions:,} |",
        f"| Total output tokens | {total_tokens:,} |",
        f"| Estimated cost | {cost_str} |",
        "",
        "### Token by Model Family",
        "",
        "| Family | Output Tokens | Share |",
        "|--------|--------------|-------|",
    ]
    for family, tokens in sorted(token_totals.items(), key=lambda x: x[1], reverse=True):
        share = f"{tokens / total_tokens * 100:.1f}%" if total_tokens else "0.0%"
        lines.append(f"| {family} | {tokens:,} | {share} |")

    lines += [
        "",
        "![daily_activity.png](images/daily_activity.png)",
        "",
        "![model_token_consumption.png](images/model_token_consumption.png)",
        "",
    ]

    # Section 7: Learnings (inserted before AI Insight)
    if learnings_data is not None and learnings_config is not None and learnings_config.get("enabled", True):
        threshold = learnings_config.get("promotion_threshold", 3)
        lines += build_learnings_report_section(learnings_data, promotion_threshold=threshold)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Saved: {output_path}")


# ── AI Insight ────────────────────────────────────────────────────────────────


def _find_prev_report(output_dir: Path, current_report: Path) -> Path | None:
    """Returns the most recent *_weekly.md in output_dir other than current_report."""
    candidates = sorted(
        [p for p in output_dir.glob("*_weekly.md") if p != current_report],
        reverse=True,
    )
    return candidates[0] if candidates else None


def _build_insight_prompt(report_text: str, prev_report_text: str, learnings_data: dict | None = None) -> str:
    """Build the prompt for AI insight generation.

    Args:
        report_text: Current week's report markdown.
        prev_report_text: Previous week's report markdown (may be empty string).
        learnings_data: Optional learnings aggregation data from parse_learnings().

    Returns:
        Prompt string to pass to the claude CLI.
    """
    sections = [
        "Analyze the following Claude Code usage report and provide a concise weekly insight.",
        "Output exactly 3-5 bullet points in this format:",
        "- [SPIKE] {change topic: quantitative observation about increases/spikes}",
        "- [DIST] {distribution topic: concentration or spread in tool/model/skill usage}",
        "- [WARN] {concern: any pattern suggesting inefficiency or risk}",
        "- [TIP] {suggestion: actionable optimization based on the data}",
        "",
        "Rules: neutral tone, data-driven, no personas, no greetings, bullets only.",
        "",
    ]

    if learnings_data is not None:
        global_tags = learnings_data.get("global_tags", Counter())
        promotion_candidates = [tag for tag, count in global_tags.most_common() if count >= 3]
        if promotion_candidates:
            tag_list = ", ".join(promotion_candidates)
            sections.append(
                f"Note: Learnings 3-strike candidates found: {tag_list}. "
                "Consider promoting these to shared rules in .claude/rules/."
            )
            sections.append("")

    sections += [
        "=== Current week report ===",
        report_text,
    ]
    if prev_report_text:
        sections += ["", "=== Previous week report (for comparison) ===", prev_report_text]
    return "\n".join(sections)


def generate_ai_insight(
    report_path: Path,
    output_dir: Path,
    config: dict,
    learnings_data: dict | None = None,
) -> None:
    """Spawns claude CLI to append AI insight to report_path. Skips on any error.

    Args:
        report_path: Path to the generated markdown report.
        output_dir: Directory containing previous reports for comparison.
        config: Full config dict with ai_insight section.
        learnings_data: Optional output from parse_learnings() for 3-strike hint injection.
    """
    ai_config = config.get("ai_insight", {})
    if not ai_config.get("enabled", False):
        print("  AI Insight: disabled (skip)")
        return

    print("Generating AI insight...")

    report_text = report_path.read_text(encoding="utf-8")
    prev_report = _find_prev_report(output_dir, report_path)
    prev_text = prev_report.read_text(encoding="utf-8") if prev_report else ""

    prompt = _build_insight_prompt(report_text, prev_text, learnings_data=learnings_data)

    try:
        import subprocess

        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and result.stdout.strip():
            insight = result.stdout.strip()
        else:
            reason = result.stderr.strip() or f"exit code {result.returncode}"
            insight = f"(insight generation skipped: {reason})"
    except FileNotFoundError:
        insight = "(insight generation skipped: claude CLI not found in PATH)"
    except subprocess.TimeoutExpired:
        insight = "(insight generation skipped: timeout)"
    except Exception as e:
        insight = f"(insight generation skipped: {e})"

    with open(report_path, "a", encoding="utf-8") as f:
        f.write(f"\n## AI Insight (Weekly Summary)\n\n{insight}\n")
    print(f"  AI Insight appended to {report_path}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(Path(args.config))
    pricing = load_pricing(config)

    since, date_range, period_label = resolve_date_range(args, config)

    project_path_str = args.project or os.environ.get("CLAUDE_PROJECT_PATH") or config.get("project_path")
    if not project_path_str:
        print(
            "ERROR: specify --project PATH, set CLAUDE_PROJECT_PATH, or set project_path in config YAML",
            file=sys.stderr,
        )
        sys.exit(1)

    project_path = Path(project_path_str).expanduser()
    if not project_path.exists():
        print(f"ERROR: project path not found: {project_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning {project_path} ({period_label}) ...")
    stats = scan_jsonl(project_path, since)
    daily_cost = compute_daily_cost(stats, pricing)

    # Parse Learnings from agent persona files
    l_config = load_learnings_config(config)
    learnings_data: dict | None = None
    if l_config["enabled"]:
        agents_dir = Path(l_config["root"])
        if agents_dir.exists():
            print(f"Parsing learnings from {agents_dir} ...")
            learnings_data = parse_learnings(agents_dir)
        else:
            print(f"  Learnings: agents dir not found ({agents_dir}), skipping")

    print("Generating charts...")
    plot_skill_usage(stats, images_dir)
    plot_agent_spawn_frequency(stats, images_dir)
    plot_mcp_usage(stats, images_dir)
    plot_tool_type_usage(stats, images_dir)
    plot_cost_daily(daily_cost, images_dir, date_range)
    plot_model_token_consumption(stats, images_dir, date_range)
    plot_daily_activity(stats, images_dir, date_range)

    report_name = f"{datetime.now().strftime('%Y-%m-%d')}_weekly.md"
    report_path = output_dir / report_name
    print("Generating report...")
    generate_report(
        stats,
        period_label,
        date_range,
        report_path,
        pricing,
        learnings_data=learnings_data,
        learnings_config=l_config,
    )

    generate_ai_insight(report_path, output_dir, config, learnings_data=learnings_data)

    print(f"\nDone! Report: {report_path}")


if __name__ == "__main__":
    main()
