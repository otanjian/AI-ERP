#!/usr/bin/env python3
"""Extract ERPNext/Frappe DocType schema and generate interactive E-R diagram HTML."""

import json
from collections import defaultdict
from pathlib import Path

BENCH_ROOT = Path(__file__).resolve().parents[1]
APPS = ["erpnext", "frappe", "hrms"]
OUTPUT = Path(__file__).resolve().parents[2] / "doc" / "erpnext-er-diagram.html"
OUTPUT_PUBLIC = (
    BENCH_ROOT
    / "apps"
    / "frappe_assistant_core"
    / "frappe_assistant_core"
    / "public"
    / "erpnext-er-diagram.html"
)

NO_DB_COLUMNS = frozenset(
    {
        "Section Break",
        "Column Break",
        "Tab Break",
        "HTML",
        "Table",
        "Table MultiSelect",
        "Button",
        "Image",
        "Fold",
        "Heading",
    }
)

STANDARD_MAIN_FIELDS = [
    {"n": "name", "t": "Data", "pk": True, "l": "主键"},
    {"n": "creation", "t": "Datetime", "l": "创建时间"},
    {"n": "modified", "t": "Datetime", "l": "修改时间"},
    {"n": "modified_by", "t": "Link", "r": "User", "l": "修改人"},
    {"n": "owner", "t": "Link", "r": "User", "l": "所有者"},
    {"n": "docstatus", "t": "Int", "l": "单据状态 (0草稿/1提交/2取消)"},
    {"n": "idx", "t": "Int", "l": "排序序号"},
]

STANDARD_CHILD_FIELDS = [
    {"n": "name", "t": "Data", "pk": True, "l": "主键"},
    {"n": "parent", "t": "Data", "fk": True, "l": "父记录 name (外键)"},
    {"n": "parenttype", "t": "Data", "l": "父 DocType"},
    {"n": "parentfield", "t": "Data", "l": "父表字段名"},
    {"n": "idx", "t": "Int", "l": "行序号"},
]


def load_doctypes():
    entities = {}
    relations = []

    for app in APPS:
        root = BENCH_ROOT / "apps" / app / app
        if not root.exists():
            continue
        for path in root.rglob("doctype/*/*.json"):
            if "chart_of_accounts" in str(path):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(data, dict) or data.get("doctype") != "DocType":
                continue

            name = data.get("name")
            if not name or data.get("is_virtual"):
                continue

            istable = bool(data.get("istable", 0))
            fields = list(STANDARD_CHILD_FIELDS if istable else STANDARD_MAIN_FIELDS)
            seen_names = {f["n"] for f in fields}

            for fld in data.get("fields", []):
                ft = fld.get("fieldtype")
                fn = fld.get("fieldname")
                if not fn or ft in NO_DB_COLUMNS:
                    if ft == "Table":
                        opts = fld.get("options", "")
                        if opts:
                            relations.append(
                                {
                                    "from": name,
                                    "field": fn,
                                    "to": opts,
                                    "type": "child",
                                    "label": fld.get("label", fn),
                                    "card": "1:N",
                                    "desc": f"{name} 包含子表 {opts}（字段 {fn}）",
                                }
                            )
                    continue

                if fn in seen_names:
                    continue
                seen_names.add(fn)

                entry = {
                    "n": fn,
                    "t": ft,
                    "l": fld.get("label", fn),
                }
                if fld.get("reqd"):
                    entry["q"] = True

                opts = fld.get("options", "")
                if ft == "Link" and opts and opts not in ("DocType",):
                    entry["r"] = opts
                    entry["fk"] = True
                    relations.append(
                        {
                            "from": name,
                            "field": fn,
                            "to": opts,
                            "type": "link",
                            "label": fld.get("label", fn),
                            "card": "N:1",
                            "desc": f"{name}.{fn} → {opts}.name",
                        }
                    )
                elif ft == "Dynamic Link":
                    entry["dynamic"] = True

                fields.append(entry)

            entities[name] = {
                "module": data.get("module", "Other"),
                "istable": istable,
                "app": app,
                "fields": fields,
            }

    return entities, relations


CORE_DOCTYPES = {
    "Accounts": [
        "Account",
        "GL Entry",
        "Journal Entry",
        "Journal Entry Account",
        "Sales Invoice",
        "Sales Invoice Item",
        "Purchase Invoice",
        "Purchase Invoice Item",
        "Payment Entry",
        "Payment Entry Reference",
        "Cost Center",
        "Fiscal Year",
        "Company",
    ],
    "Selling": [
        "Customer",
        "Quotation",
        "Quotation Item",
        "Sales Order",
        "Sales Order Item",
        "Delivery Note",
        "Delivery Note Item",
        "Sales Taxes and Charges",
    ],
    "Buying": [
        "Supplier",
        "Request for Quotation",
        "Supplier Quotation",
        "Purchase Order",
        "Purchase Order Item",
        "Purchase Receipt",
        "Purchase Receipt Item",
    ],
    "Stock": [
        "Item",
        "Item Group",
        "Warehouse",
        "Stock Entry",
        "Stock Entry Detail",
        "Stock Ledger Entry",
        "Bin",
        "Batch",
        "Serial No",
        "UOM",
    ],
    "Manufacturing": [
        "BOM",
        "BOM Item",
        "BOM Operation",
        "Work Order",
        "Work Order Item",
        "Job Card",
        "Operation",
        "Workstation",
    ],
    "CRM": ["Lead", "Opportunity", "Campaign"],
    "Projects": ["Project", "Task", "Timesheet", "Timesheet Detail"],
    "HR": ["Employee", "Department", "Designation", "Salary Slip"],
}


def mermaid_id(name):
    return "".join(c if c.isalnum() else "_" for c in name)


def mermaid_type(ft):
    mapping = {
        "Data": "string",
        "Int": "int",
        "Long Int": "int",
        "Float": "float",
        "Currency": "float",
        "Percent": "float",
        "Check": "boolean",
        "Date": "date",
        "Datetime": "datetime",
        "Time": "time",
        "Text": "text",
        "Small Text": "text",
        "Long Text": "text",
        "Select": "string",
        "Link": "string",
        "Dynamic Link": "string",
        "Password": "string",
        "JSON": "text",
    }
    return mapping.get(ft, "string")


def build_mermaid_er(entities, relations, doctype_set, mode="all"):
    """mode: all | links | children"""
    lines = ["erDiagram"]
    edge_fields = defaultdict(list)

    for rel in relations:
        src, tgt = rel["from"], rel["to"]
        if src not in doctype_set:
            continue
        if rel["type"] == "child":
            if mode == "links":
                continue
            if tgt not in doctype_set:
                continue
            edge_fields[(tgt, src, "child")].append(rel["field"])
        else:
            if mode == "children":
                continue
            if tgt not in doctype_set:
                continue
            edge_fields[(src, tgt, "link")].append(rel["field"])

    for (src, tgt, rtype), field_names in sorted(edge_fields.items()):
        src_id, tgt_id = mermaid_id(src), mermaid_id(tgt)
        label = ", ".join(sorted(set(field_names))[:3])
        if len(set(field_names)) > 3:
            label += "…"
        if rtype == "child":
            lines.append(f'    {src_id} ||--o{{ {tgt_id} : "{label}"')
        else:
            lines.append(f'    {src_id} }}o--|| {tgt_id} : "{label}"')

    for dt in sorted(doctype_set):
        if dt not in entities:
            continue
        meta = entities[dt]
        if mode == "links" and meta["istable"]:
            continue
        dt_id = mermaid_id(dt)
        lines.append(f"    {dt_id} {{")
        for f in meta["fields"]:
            tags = []
            if f.get("pk"):
                tags.append("PK")
            if f.get("fk"):
                tags.append(f'FK "{f["r"]}"' if f.get("r") else "FK")
            suffix = " ".join(tags)
            col = f"{mermaid_type(f['t'])} {f['n']}"
            if suffix:
                col += f" {suffix}"
            lines.append(f"        {col}")
        lines.append("    }")

    return "\n".join(lines)


def generate_html(entities, relations):
    modules = sorted({e["module"] for e in entities.values() if e["module"]})
    module_counts = defaultdict(int)
    for e in entities.values():
        module_counts[e["module"]] += 1

    core_diagrams = {}
    for group, doctypes in CORE_DOCTYPES.items():
        dt_set = set(doctypes)
        core_diagrams[group] = {
            "all": build_mermaid_er(entities, relations, dt_set, "all"),
            "links": build_mermaid_er(entities, relations, dt_set, "links"),
            "children": build_mermaid_er(entities, relations, dt_set, "children"),
        }

    # Build adjacency for graph view
    adjacency = defaultdict(list)
    for rel in relations:
        if rel["type"] == "link":
            adjacency[rel["from"]].append(rel)
            adjacency[rel["to"]].append(
                {**rel, "from": rel["to"], "to": rel["from"], "type": "inbound_link"}
            )
        else:
            adjacency[rel["from"]].append(rel)
            adjacency[rel["to"]].append(
                {**rel, "from": rel["to"], "to": rel["from"], "type": "inbound_child", "field": "parent"}
            )

    payload = {
        "entities": entities,
        "relations": relations,
        "modules": modules,
        "moduleCounts": dict(module_counts),
        "coreDiagrams": core_diagrams,
        "adjacency": {k: v for k, v in adjacency.items()},
    }
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ERPNext 数据库 E-R 图</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
  <style>
    :root {{
      --bg: #0f1419; --surface: #1a2332; --surface2: #243044;
      --border: #2d3a4f; --text: #e6edf3; --muted: #8b9cb3;
      --accent: #3b82f6; --accent2: #10b981; --child: #f59e0b; --inbound: #a78bfa;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ height: 100%; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
      background: var(--bg); color: var(--text); line-height: 1.5; min-height: 100vh;
      display: flex; flex-direction: column; overflow: hidden; }}
    header {{ padding: 1.25rem 2rem; border-bottom: 1px solid var(--border);
      background: linear-gradient(135deg, #1a2332 0%, #0f1419 100%); }}
    header h1 {{ font-size: 1.4rem; }}
    header p {{ color: var(--muted); margin-top: 0.3rem; font-size: 0.85rem; }}
    .stats {{ display: flex; gap: 1rem; margin-top: 0.75rem; flex-wrap: wrap; }}
    .stat {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem 0.9rem; font-size: 0.8rem; }}
    .stat strong {{ color: var(--accent); font-size: 1rem; display: block; }}
    nav.tabs {{ display: flex; gap: 0.4rem; padding: 0.75rem 2rem; border-bottom: 1px solid var(--border);
      flex-wrap: wrap; background: var(--surface); }}
    nav.tabs button {{ background: transparent; border: 1px solid var(--border); color: var(--muted);
      padding: 0.4rem 0.85rem; border-radius: 6px; cursor: pointer; font-size: 0.82rem; }}
    nav.tabs button.active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
    main {{ flex: 1; min-height: 0; padding: 1rem 2rem 0.5rem; display: flex; flex-direction: column; overflow: hidden; }}
    .panel {{ display: none; flex-direction: column; min-height: 0; }}
    .panel.active {{ display: flex; flex: 1; }}
    .panel:not(#panel-graph).active {{ overflow-y: auto; }}
    #panel-graph.panel.active {{ overflow: hidden; }}
    h2.section {{ font-size: 1.05rem; margin-bottom: 0.5rem; flex-shrink: 0; }}
    .graph-toolbar {{ flex-shrink: 0; }}
    .graph-hint {{ color: var(--muted); font-size: 0.75rem; margin: 0.35rem 0 0.5rem; flex-shrink: 0; }}
    .controls {{ display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; align-items: center; }}
    .controls input, .controls select {{ background: var(--surface); border: 1px solid var(--border);
      color: var(--text); padding: 0.45rem 0.7rem; border-radius: 6px; font-size: 0.85rem; }}
    .controls label {{ font-size: 0.82rem; color: var(--muted); display: flex; align-items: center; gap: 0.35rem; }}
    .viz-box {{ position: relative; border-radius: 10px; border: 1px solid var(--border); background: #fff; }}
    .viz-box .viz-body {{ width: 100%; }}
    #graph-viz-box {{ flex: 1; min-height: 0; display: flex; flex-direction: column; }}
    #graph-network.viz-body {{ flex: 1; min-height: 0; height: 100% !important; }}
    .diagram-wrap.viz-body {{ padding: 1rem; overflow: auto; min-height: 400px; }}
    .fs-btn {{
      position: absolute; top: 0.5rem; right: 0.5rem; z-index: 10;
      background: rgba(15,20,25,0.75); color: #fff; border: 1px solid var(--border);
      padding: 0.35rem 0.65rem; border-radius: 6px; cursor: pointer; font-size: 0.78rem;
      backdrop-filter: blur(4px);
    }}
    .fs-btn:hover {{ background: var(--accent); border-color: var(--accent); }}
    .viz-box:fullscreen {{
      border-radius: 0; border: none; background: #fff;
      display: flex; flex-direction: column; width: 100vw; height: 100vh;
    }}
    .viz-box:fullscreen .viz-body {{ flex: 1; height: auto !important; min-height: 0; overflow: auto; }}
    .viz-box:fullscreen .fs-btn {{ top: 0.75rem; right: 0.75rem; }}
    .viz-box:fullscreen .fs-hint {{
      position: absolute; bottom: 0.75rem; left: 50%; transform: translateX(-50%);
      color: var(--muted); font-size: 0.75rem; pointer-events: none;
    }}
    .legend {{ display: flex; gap: 1.2rem; margin-bottom: 0.75rem; font-size: 0.78rem; color: var(--muted); flex-wrap: wrap; }}
    .legend i {{ display: inline-block; width: 28px; height: 3px; margin-right: 0.3rem; vertical-align: middle; }}
    .legend .lk i {{ background: var(--accent2); }}
    .legend .ch i {{ background: var(--child); border-style: dashed; }}
    .legend .pk {{ color: #fbbf24; }}
    .legend .fk {{ color: var(--accent2); }}
    .core-tabs, .mode-tabs {{ display: flex; gap: 0.35rem; flex-wrap: wrap; margin-bottom: 0.75rem; }}
    .core-tabs button, .mode-tabs button {{ background: var(--surface); border: 1px solid var(--border);
      color: var(--muted); padding: 0.3rem 0.7rem; border-radius: 6px; cursor: pointer; font-size: 0.78rem; }}
    .core-tabs button.active {{ background: var(--accent2); border-color: var(--accent2); color: #fff; }}
    .mode-tabs button.active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 0.75rem; }}
    .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 0.85rem; cursor: pointer; }}
    .card:hover {{ border-color: var(--accent); }}
    .card h3 {{ font-size: 0.9rem; }}
    .card .meta {{ font-size: 0.72rem; color: var(--muted); margin-top: 0.25rem; }}
    .badge {{ display: inline-block; font-size: 0.68rem; padding: 0.1rem 0.4rem; border-radius: 3px; margin-right: 0.25rem; }}
    .badge-table {{ background: #1e3a5f; color: #93c5fd; }}
    .badge-child {{ background: #422006; color: var(--child); }}
    .badge-module {{ background: #1a2e1a; color: var(--accent2); }}
    .detail-panel {{ position: fixed; right: 0; top: 0; width: min(560px, 100vw); height: 100vh;
      background: var(--surface); border-left: 1px solid var(--border); padding: 1.25rem;
      overflow-y: auto; transform: translateX(100%); transition: transform 0.25s; z-index: 200; }}
    .detail-panel.open {{ transform: translateX(0); }}
    .detail-panel .close {{ position: absolute; top: 0.75rem; right: 0.75rem; background: none;
      border: none; color: var(--muted); font-size: 1.5rem; cursor: pointer; }}
  .schema-table {{ width: 100%; border-collapse: collapse; font-size: 0.78rem; margin-top: 0.5rem; }}
    .schema-table th {{ text-align: left; padding: 0.4rem 0.5rem; background: var(--surface2);
      border-bottom: 1px solid var(--border); position: sticky; top: 0; }}
    .schema-table td {{ padding: 0.35rem 0.5rem; border-bottom: 1px solid var(--border); }}
    .schema-table tr:hover td {{ background: var(--surface2); }}
    .schema-table code {{ color: #93c5fd; }}
    .tag-pk {{ color: #fbbf24; font-size: 0.68rem; margin-left: 0.25rem; }}
    .tag-fk {{ color: var(--accent2); font-size: 0.68rem; margin-left: 0.25rem; }}
    .tag-req {{ color: #f87171; font-size: 0.68rem; }}
    .rel-section {{ margin-top: 1rem; }}
    .rel-section h4 {{ font-size: 0.82rem; color: var(--muted); margin-bottom: 0.4rem; }}
    .rel-card {{ background: var(--surface2); border-radius: 6px; padding: 0.5rem 0.65rem;
      margin-bottom: 0.4rem; font-size: 0.78rem; cursor: pointer; border-left: 3px solid var(--border); }}
    .rel-card.link {{ border-left-color: var(--accent2); }}
    .rel-card.child {{ border-left-color: var(--child); }}
    .rel-card:hover {{ background: #2a3a52; }}
    .rel-card .arrow {{ color: var(--muted); margin: 0 0.3rem; }}
    .rel-card .card-label {{ color: var(--muted); font-size: 0.7rem; }}
    .module-list {{ columns: 3; column-gap: 2rem; list-style: none; }}
    .module-list li {{ break-inside: avoid; padding: 0.2rem 0; font-size: 0.82rem; color: var(--muted); }}
    .split {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    @media (max-width: 900px) {{ .split {{ grid-template-columns: 1fr; }} .module-list {{ columns: 1; }} }}
  </style>
</head>
<body>
  <header>
    <h1>ERPNext 数据库实体关系图</h1>
    <p>完整字段 + 清晰表间关系 · 数据库表名 <code>tab&#123;DocType&#125;</code> · Link=N:1外键 · Table=1:N子表</p>
    <div class="stats" id="stats"></div>
  </header>

  <nav class="tabs">
    <button class="active" data-tab="graph">关系图谱</button>
    <button data-tab="core">模块 E-R 图</button>
    <button data-tab="table">表结构详情</button>
    <button data-tab="browse">浏览全部表</button>
    <button data-tab="relations">关系清单</button>
    <button data-tab="modules">模块统计</button>
  </nav>

  <main>
    <section id="panel-graph" class="panel active">
      <div class="graph-toolbar">
        <h2 class="section">交互式表关系图谱</h2>
        <div class="legend">
          <span class="lk"><i></i>实线 = Link 外键 (N:1)</span>
          <span class="ch"><i style="border-top:2px dashed var(--child);height:0;background:none"></i>虚线 = 子表 (1:N)</span>
          <span>边上标注为关联字段名</span>
        </div>
        <div class="controls">
          <select id="graph-center" style="min-width:220px"></select>
          <select id="graph-depth">
            <option value="1" selected>展开 1 层关系</option>
            <option value="2">展开 2 层关系</option>
            <option value="3">展开 3 层关系</option>
          </select>
          <label><input type="checkbox" id="graph-show-link" checked /> Link 外键</label>
          <label><input type="checkbox" id="graph-show-child" checked /> 子表</label>
          <label><input type="checkbox" id="graph-main-only" /> 仅主表</label>
        </div>
        <p class="graph-hint">
          <strong id="graph-center-label" style="color:var(--accent2)"></strong>
          · 点击节点以该表为中心重新展开 · 拖拽平移 · 滚轮缩放
        </p>
      </div>
      <div class="viz-box" id="graph-viz-box">
        <button type="button" class="fs-btn" data-fs-target="graph-viz-box" title="全屏 (Esc 退出)">⛶ 全屏</button>
        <div id="graph-network" class="viz-body"></div>
        <span class="fs-hint" style="display:none">Esc 退出全屏 · 点击节点以该表为中心展开 · 拖拽平移 · 滚轮缩放</span>
      </div>
    </section>

    <section id="panel-core" class="panel">
      <h2 class="section">核心业务模块 E-R 图（含完整字段）</h2>
      <div class="legend">
        <span><code>}}o--||</code> N:1 Link 外键</span>
        <span><code>||--o{{</code> 1:N 子表</span>
        <span class="pk">PK</span><span class="fk">FK</span> 标注在字段后
      </div>
      <div class="core-tabs" id="core-tabs"></div>
      <div class="mode-tabs" id="mode-tabs">
        <button class="active" data-mode="all">全部关系</button>
        <button data-mode="links">仅主表外键</button>
        <button data-mode="children">仅主子表</button>
      </div>
      <div class="viz-box" id="core-viz-box">
        <button type="button" class="fs-btn" data-fs-target="core-viz-box" title="全屏 (Esc 退出)">⛶ 全屏</button>
        <div class="diagram-wrap viz-body"><pre class="mermaid" id="core-diagram"></pre></div>
        <span class="fs-hint" style="display:none">Esc 退出全屏</span>
      </div>
    </section>

    <section id="panel-table" class="panel">
      <h2 class="section">单表完整结构</h2>
      <div class="controls">
        <select id="table-select" style="min-width:280px"></select>
      </div>
      <div id="table-detail"></div>
    </section>

    <section id="panel-browse" class="panel">
      <div class="controls">
        <input type="search" id="search" placeholder="搜索表名 / 模块..." style="min-width:240px" />
        <select id="module-filter"><option value="">全部模块</option></select>
        <select id="type-filter">
          <option value="">全部类型</option>
          <option value="table">主表</option>
          <option value="child">子表</option>
        </select>
      </div>
      <div class="grid" id="entity-grid"></div>
    </section>

    <section id="panel-relations" class="panel">
      <div class="controls">
        <input type="search" id="rel-search" placeholder="搜索源表、目标表、字段..." style="min-width:240px" />
        <select id="rel-type-filter">
          <option value="">全部类型</option>
          <option value="link">Link 外键 (N:1)</option>
          <option value="child">子表 (1:N)</option>
        </select>
      </div>
      <div id="rel-table-wrap" style="overflow:auto;max-height:75vh"></div>
    </section>

    <section id="panel-modules" class="panel">
      <h2 class="section">模块 DocType 数量</h2>
      <ul class="module-list" id="module-list"></ul>
    </section>
  </main>

  <aside class="detail-panel" id="detail">
    <button class="close" id="detail-close">&times;</button>
    <div id="detail-content"></div>
  </aside>

  <script id="schema-data" type="application/json">{payload_json}</script>
  <script>
    const DATA = JSON.parse(document.getElementById('schema-data').textContent);
    const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

    mermaid.initialize({{ startOnLoad: false, theme: 'default', er: {{ useMaxWidth: false }}, securityLevel: 'loose' }});

    // ── Fullscreen ──
    function toggleFullscreen(boxId) {{
      const box = document.getElementById(boxId);
      if (!box) return;
      if (document.fullscreenElement === box) {{
        document.exitFullscreen();
      }} else {{
        box.requestFullscreen().catch(() => {{}});
      }}
    }}
    document.querySelectorAll('.fs-btn').forEach(btn => {{
      btn.addEventListener('click', e => {{ e.stopPropagation(); toggleFullscreen(btn.dataset.fsTarget); }});
    }});
    document.addEventListener('fullscreenchange', () => {{
      document.querySelectorAll('.viz-box').forEach(box => {{
        const inFs = document.fullscreenElement === box;
        const hint = box.querySelector('.fs-hint');
        const btn = box.querySelector('.fs-btn');
        if (hint) hint.style.display = inFs ? 'block' : 'none';
        if (btn) btn.textContent = inFs ? '✕ 退出全屏' : '⛶ 全屏';
      }});
      if (typeof network !== 'undefined' && network) {{
        setTimeout(() => network.fit({{ animation: true }}), 100);
      }}
    }});

    // ── Stats ──
    const mainN = Object.values(DATA.entities).filter(e => !e.istable).length;
    const childN = Object.values(DATA.entities).filter(e => e.istable).length;
    const linkN = DATA.relations.filter(r => r.type === 'link').length;
    const childRelN = DATA.relations.filter(r => r.type === 'child').length;
    document.getElementById('stats').innerHTML = [
      ['DocType', Object.keys(DATA.entities).length],
      ['主表', mainN], ['子表', childN],
      ['Link外键', linkN], ['子表关系', childRelN]
    ].map(([l,v]) => `<div class="stat"><strong>${{v}}</strong>${{l}}</div>`).join('');

    // ── Tabs ──
    document.querySelectorAll('nav.tabs button').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('nav.tabs button').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
      }});
    }});

    // ── Field table renderer ──
    function renderFieldTable(fields) {{
      return `<table class="schema-table"><thead><tr>
        <th>字段名</th><th>类型</th><th>关联</th><th>说明</th>
      </tr></thead><tbody>${{fields.map(f => {{
        const tags = (f.pk ? '<span class="tag-pk">PK</span>' : '') +
          (f.fk ? '<span class="tag-fk">FK→'+esc(f.r||'')+'</span>' : '') +
          (f.q ? '<span class="tag-req">必填</span>' : '');
        const ref = f.r ? `<a href="#" onclick="showDetail('${{esc(f.r).replace(/'/g,"\\\\'")}}');return false">${{esc(f.r)}}</a>` : (f.dynamic ? '动态' : '');
        return `<tr><td><code>${{esc(f.n)}}</code>${{tags}}</td><td>${{esc(f.t)}}</td><td>${{ref}}</td><td>${{esc(f.l||'')}}</td></tr>`;
      }}).join('')}}</tbody></table>`;
    }}

    function renderRelationsBlock(name) {{
      const out = DATA.relations.filter(r => r.from === name);
      const inn = DATA.relations.filter(r => r.to === name && r.type === 'link');
      const childOf = DATA.relations.filter(r => r.to === name && r.type === 'child');
      let html = '';
      if (out.length) {{
        html += '<div class="rel-section"><h4>本表指向其他表 ('+out.length+')</h4>';
        out.forEach(r => {{
          html += `<div class="rel-card ${{r.type}}" onclick="focusOnTable('${{esc(r.to).replace(/'/g,"\\\\'")}}')">
            <code>${{esc(r.field)}}</code> <span class="arrow">→</span> <strong>${{esc(r.to)}}</strong>
            <div class="card-label">${{r.type==='link' ? 'Link N:1' : '子表 1:N'}} · ${{esc(r.desc)}}</div></div>`;
        }});
        html += '</div>';
      }}
      if (inn.length) {{
        html += '<div class="rel-section"><h4>其他表引用本表 ('+inn.length+')</h4>';
        inn.forEach(r => {{
          html += `<div class="rel-card link" onclick="focusOnTable('${{esc(r.from).replace(/'/g,"\\\\'")}}')">
            <strong>${{esc(r.from)}}</strong>.<code>${{esc(r.field)}}</code> <span class="arrow">→</span> 本表
            <div class="card-label">Link N:1 · ${{esc(r.desc)}}</div></div>`;
        }});
        html += '</div>';
      }}
      if (childOf.length) {{
        html += '<div class="rel-section"><h4>以本表为父表的子表 ('+childOf.length+')</h4>';
        childOf.forEach(r => {{
          html += `<div class="rel-card child" onclick="focusOnTable('${{esc(r.from).replace(/'/g,"\\\\'")}}')">
            <strong>${{esc(r.from)}}</strong> 包含子表 <strong>${{esc(r.to)}}</strong>（字段 <code>${{esc(r.field)}}</code>）
            <div class="card-label">1:N · parent 指向 ${{esc(r.from)}}.name</div></div>`;
        }});
        html += '</div>';
      }}
      return html || '<p style="color:var(--muted);font-size:0.82rem">无关联关系</p>';
    }}

  window.showDetail = function(name) {{
      const e = DATA.entities[name];
      if (!e) return;
      document.getElementById('detail-content').innerHTML = `
        <h2 style="font-size:1.1rem">${{esc(name)}}</h2>
        <p style="color:var(--muted);font-size:0.82rem;margin:0.4rem 0">
          表名: <code>tab${{esc(name.replace(/ /g,''))}}</code> · ${{esc(e.module)}} · ${{e.istable?'子表':'主表'}}
        </p>
        <h3 style="font-size:0.88rem;margin-top:0.75rem">全部字段 (${{e.fields.length}})</h3>
        ${{renderFieldTable(e.fields)}}
        ${{renderRelationsBlock(name)}}
      `;
      document.getElementById('detail').classList.add('open');
    }};
    document.getElementById('detail-close').onclick = () => document.getElementById('detail').classList.remove('open');

    // ── Table detail panel ──
    const tableSelect = document.getElementById('table-select');
    Object.keys(DATA.entities).sort().forEach(n => {{
      const o = document.createElement('option'); o.value = n; o.textContent = n; tableSelect.appendChild(o);
    }});
    function renderTableDetail() {{
      const name = tableSelect.value;
      const e = DATA.entities[name];
      if (!e) return;
      document.getElementById('table-detail').innerHTML = `
        <h3 style="margin-bottom:0.5rem">${{esc(name)}} <span style="color:var(--muted);font-size:0.82rem">(${{e.fields.length}} 字段)</span></h3>
        ${{renderFieldTable(e.fields)}}
        <div style="margin-top:1.25rem">${{renderRelationsBlock(name)}}</div>
      `;
    }}
    tableSelect.onchange = renderTableDetail;
    tableSelect.value = 'Sales Order';
    renderTableDetail();

    // ── Interactive graph ──
    const graphCenter = document.getElementById('graph-center');
    Object.keys(DATA.entities).sort().forEach(n => {{
      const o = document.createElement('option'); o.value = n; o.textContent = n; graphCenter.appendChild(o);
    }});
    graphCenter.value = 'Sales Order';
    let network = null;
    let graphNodes = null;
    let currentGraphCenter = 'Sales Order';

    function updateCenterLabel(name) {{
      const el = document.getElementById('graph-center-label');
      if (el) el.textContent = '中心表: ' + name;
    }}

    function buildGraph(center, depth) {{
      const showLink = document.getElementById('graph-show-link').checked;
      const showChild = document.getElementById('graph-show-child').checked;
      const mainOnly = document.getElementById('graph-main-only').checked;
      const nodes = new Map();
      const edges = [];
      const edgeSet = new Set();

      function addNode(n) {{
        if (!DATA.entities[n]) return;
        if (mainOnly && DATA.entities[n].istable) return;
        if (!nodes.has(n)) {{
          const e = DATA.entities[n];
          const isCenter = n === center;
          nodes.set(n, {{
            id: n, label: n.replace(/ /g, '\\n'),
            color: isCenter
              ? {{ background: '#fbbf24', border: '#d97706', highlight: {{ background: '#fcd34d', border: '#d97706' }} }}
              : (e.istable ? '#fef3c7' : '#dbeafe'),
            borderWidth: isCenter ? 4 : 1,
            size: isCenter ? 28 : (e.istable ? 18 : 22),
            font: {{ size: isCenter ? 13 : 11, bold: isCenter }},
            shape: e.istable ? 'box' : 'ellipse',
            ...(isCenter ? {{ x: 0, y: 0, fixed: {{ x: true, y: true }} }} : {{}}),
          }});
        }}
      }}

      function expand(from, d) {{
        addNode(from);
        if (d <= 0) return;
        (DATA.adjacency[from] || []).forEach(rel => {{
          if (rel.type === 'link' && !showLink) return;
          if (rel.type === 'child' && !showChild) return;
          if (rel.type.startsWith('inbound') && rel.type.includes('child') && !showChild) return;
          if (rel.type.startsWith('inbound') && rel.type.includes('link') && !showLink) return;
          const to = rel.to;
          if (mainOnly && DATA.entities[to]?.istable) return;
          const isChild = rel.type === 'child' || rel.type === 'inbound_child';
          const isInboundLink = rel.type === 'inbound_link';
          let edgeFrom, edgeTo;
          if (isChild) {{
            edgeFrom = rel.type === 'child' ? rel.from : rel.to;
            edgeTo = rel.type === 'child' ? rel.to : rel.from;
          }} else if (isInboundLink) {{
            edgeFrom = rel.to;
            edgeTo = rel.from;
          }} else {{
            edgeFrom = rel.from;
            edgeTo = rel.to;
          }}
          const eid = edgeFrom + '|' + rel.field + '|' + edgeTo + '|' + (isChild ? 'child' : 'link');
          if (!edgeSet.has(eid)) {{
            edgeSet.add(eid);
            edges.push({{
              from: edgeFrom,
              to: edgeTo,
              label: rel.field,
              arrows: 'to',
              color: {{ color: isChild ? '#f59e0b' : '#10b981' }},
              dashes: isChild,
              font: {{ align: 'middle', size: 10 }},
              title: rel.desc || '',
            }});
          }}
          addNode(to);
          if (d > 1) expand(to, d - 1);
        }});
      }}

      expand(center, parseInt(depth, 10));
      return {{ nodes: Array.from(nodes.values()), edges }};
    }}

    function focusOnTable(name, opts = {{}}) {{
      if (!DATA.entities[name]) return;
      currentGraphCenter = name;
      graphCenter.value = name;
      updateCenterLabel(name);
      renderGraph();
      if (opts.showDetail !== false) showDetail(name);
    }}
    window.focusOnTable = focusOnTable;

    function renderGraph() {{
      const center = currentGraphCenter || graphCenter.value;
      currentGraphCenter = center;
      updateCenterLabel(center);
      const built = buildGraph(center, document.getElementById('graph-depth').value);
      const container = document.getElementById('graph-network');
      if (network) network.destroy();
      graphNodes = new vis.DataSet(built.nodes);
      network = new vis.Network(container, {{ nodes: graphNodes, edges: built.edges }}, {{
        physics: {{
          enabled: true,
          barnesHut: {{
            gravitationalConstant: -4000,
            centralGravity: 0.45,
            springLength: 180,
            springConstant: 0.05,
            avoidOverlap: 0.2,
          }},
          stabilization: {{ iterations: 120, fit: true }},
        }},
        interaction: {{ hover: true, tooltipDelay: 120 }},
        edges: {{ smooth: {{ type: 'cubicBezier' }}, font: {{ size: 10 }} }},
      }});

      network.once('stabilizationIterationsDone', () => {{
        network.focus(center, {{
          scale: built.nodes.length > 25 ? 0.55 : (built.nodes.length > 12 ? 0.75 : 1.0),
          animation: {{ duration: 450, easingFunction: 'easeInOutQuad' }},
        }});
      }});

      network.on('click', p => {{
        if (p.nodes.length) focusOnTable(p.nodes[0]);
      }});
    }}
    graphCenter.onchange = () => focusOnTable(graphCenter.value, {{ showDetail: false }});
    document.getElementById('graph-depth').onchange = renderGraph;
    ['graph-show-link','graph-show-child','graph-main-only'].forEach(id =>
      document.getElementById(id).onchange = renderGraph);
    focusOnTable('Sales Order', {{ showDetail: false }});
    window.addEventListener('resize', () => {{ if (network) network.redraw(); }});

    // ── Core mermaid ──
    const coreGroups = Object.keys(DATA.coreDiagrams);
    const coreTabs = document.getElementById('core-tabs');
    const modeTabs = document.getElementById('mode-tabs');
    const coreDiagram = document.getElementById('core-diagram');
    let activeGroup = coreGroups[0], activeMode = 'all';

    function renderCore() {{
      coreTabs.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.group === activeGroup));
      modeTabs.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.mode === activeMode));
      coreDiagram.removeAttribute('data-processed');
      coreDiagram.textContent = DATA.coreDiagrams[activeGroup][activeMode];
      mermaid.run({{ nodes: [coreDiagram] }}).catch(e => {{ coreDiagram.textContent = '图表过大，请使用「关系图谱」或「表结构详情」查看'; }});
    }}
    coreGroups.forEach((g,i) => {{
      const btn = document.createElement('button');
      btn.textContent = g; btn.dataset.group = g;
      if (i===0) btn.classList.add('active');
      btn.onclick = () => {{ activeGroup = g; renderCore(); }};
      coreTabs.appendChild(btn);
    }});
    modeTabs.querySelectorAll('button').forEach(btn => {{
      btn.onclick = () => {{ activeMode = btn.dataset.mode; renderCore(); }};
    }});
    renderCore();

    // ── Browse grid ──
    const moduleFilter = document.getElementById('module-filter');
    DATA.modules.forEach(m => {{
      const o = document.createElement('option');
      o.value = m; o.textContent = m + ' (' + (DATA.moduleCounts[m]||0) + ')';
      moduleFilter.appendChild(o);
    }});
    const grid = document.getElementById('entity-grid');
    function renderGrid() {{
      const q = document.getElementById('search').value.toLowerCase();
      const mod = moduleFilter.value, typ = document.getElementById('type-filter').value;
      grid.innerHTML = '';
      Object.entries(DATA.entities).filter(([name,e]) => {{
        if (mod && e.module !== mod) return false;
        if (typ==='table' && e.istable) return false;
        if (typ==='child' && !e.istable) return false;
        if (q && !name.toLowerCase().includes(q) && !(e.module||'').toLowerCase().includes(q)) return false;
        return true;
      }}).sort((a,b)=>a[0].localeCompare(b[0])).forEach(([name,e]) => {{
        const card = document.createElement('div');
        card.className = 'card';
        const outN = DATA.relations.filter(r=>r.from===name).length;
        card.innerHTML = `<h3>${{esc(name)}}</h3><div class="meta">
          <span class="badge ${{e.istable?'badge-child':'badge-table'}}">${{e.istable?'子表':'主表'}}</span>
          <span class="badge badge-module">${{esc(e.module)}}</span>
          ${{e.fields.length}} 字段 · ${{outN}} 出站关联</div>`;
        card.onclick = () => showDetail(name);
        grid.appendChild(card);
      }});
    }}
    document.getElementById('search').oninput = renderGrid;
    moduleFilter.onchange = renderGrid;
    document.getElementById('type-filter').onchange = renderGrid;
    renderGrid();

    // ── Relations list ──
    function renderRelations() {{
      const q = document.getElementById('rel-search').value.toLowerCase();
      const typ = document.getElementById('rel-type-filter').value;
      const rows = DATA.relations.filter(r => {{
        if (typ && r.type !== typ) return false;
        if (!q) return true;
        return r.from.toLowerCase().includes(q) || r.to.toLowerCase().includes(q) ||
          r.field.toLowerCase().includes(q) || (r.desc||'').toLowerCase().includes(q);
      }});
      const show = rows.slice(0, 1000);
      document.getElementById('rel-table-wrap').innerHTML = `
        <p style="color:var(--muted);font-size:0.78rem;margin-bottom:0.5rem">共 ${{rows.length}} 条关系${{rows.length>1000?'，显示前1000条':''}}</p>
        <table class="schema-table"><thead><tr>
          <th>源表</th><th>字段</th><th>关系</th><th>基数</th><th>目标表</th><th>说明</th>
        </tr></thead><tbody>${{show.map(r => `<tr style="cursor:pointer" onclick="showDetail('${{esc(r.from).replace(/'/g,"\\\\'")}}')">
          <td><strong>${{esc(r.from)}}</strong></td>
          <td><code>${{esc(r.field)}}</code></td>
          <td>${{r.type==='link'?'<span style="color:var(--accent2)">Link</span>':'<span style="color:var(--child)">子表</span>'}}</td>
          <td>${{esc(r.card)}}</td>
          <td><a href="#" onclick="showDetail('${{esc(r.to).replace(/'/g,"\\\\'")}}');return false">${{esc(r.to)}}</a></td>
          <td style="color:var(--muted)">${{esc(r.desc)}}</td>
        </tr>`).join('')}}</tbody></table>`;
    }}
    document.getElementById('rel-search').oninput = renderRelations;
    document.getElementById('rel-type-filter').onchange = renderRelations;
    renderRelations();

    // ── Module list ──
    const ml = document.getElementById('module-list');
    DATA.modules.sort((a,b)=>(DATA.moduleCounts[b]||0)-(DATA.moduleCounts[a]||0))
      .forEach(m => {{ const li = document.createElement('li'); li.innerHTML = `<strong>${{esc(m)}}</strong> — ${{DATA.moduleCounts[m]}} 个`; ml.appendChild(li); }});
  </script>
</body>
</html>
"""


def main():
    entities, relations = load_doctypes()
    html = generate_html(entities, relations)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    OUTPUT_PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PUBLIC.write_text(html, encoding="utf-8")
    print(f"Generated: {OUTPUT}")
    print(f"Published: {OUTPUT_PUBLIC}")
    print(f"  Entities: {len(entities)}")
    print(f"  Relations: {len(relations)} (link: {sum(1 for r in relations if r['type']=='link')}, child: {sum(1 for r in relations if r['type']=='child')})")
    so = entities.get("Sales Order")
    if so:
        print(f"  Sales Order fields: {len(so['fields'])}")


if __name__ == "__main__":
    main()
