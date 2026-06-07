# AI-ERP

基于 [Frappe Bench](https://frappeframework.com/docs/user/en/bench) 的企业资源规划（ERP）本地开发环境，集成 **ERPNext v16** 与 **AI 助手**（Frappe Assistant Core），并附带制造行业样板间数据脚本与运维工具。

| 项目 | 说明 |
|------|------|
| 仓库 | [github.com/otanjian/AI-ERP](https://github.com/otanjian/AI-ERP) |
| 默认站点 | `west.bosofts.com` |
| Desk 入口 | http://localhost:8000/desk/ |
| 内部 Web 端口 | http://localhost:18000 |

---

## 功能概览

- **ERPNext 全模块**：财务、库存、采购、销售、制造、项目等
- **AI 助手面板**：Desk 右侧 iframe 嵌入外部 Agent；支持 MCP 对接 LLM（Claude、ChatGPT 等）
- **制造样板间**：一键导入「智联电脑组装有限公司」演示数据（科目、主数据、完整业务流）
- **本地运维**：自动构建前端资源、Desk 守护进程、一键修复脚本

---

## 技术栈

| 组件 | 版本 / 说明 |
|------|-------------|
| Frappe Framework | 16.x |
| ERPNext | 16.x |
| Python | 3.11+（`env/` 虚拟环境） |
| MariaDB | 本地 socket：`/tmp/mysql.sock` |
| Redis | 缓存 + 队列 + Socket.IO |
| Node.js | Frappe 前端构建、Socket.IO |

### 已安装应用

| 应用 | 用途 |
|------|------|
| `frappe` | 框架核心 |
| `erpnext` | ERP 业务模块 |
| `frappe_assistant_core` | AI 助手（iframe + MCP） |
| `hrms` | 人力资源 |
| `crm` | 客户关系 |
| `helpdesk` | 工单支持 |
| `insights` | 数据分析 |
| `wiki` | 知识库 |
| `telephony` | 电话集成 |

应用列表见 `sites/apps.txt`，版本锁定见 `sites/apps.json`。

---

## 目录结构

本仓库（`frappe-bench/`）是 Bench 本体；上层工作区（`../`）存放启动脚本与业务文档。

```
../                              # Cursor 工作区根目录
├── start.sh                     # 一键启动（推荐入口）
├── scripts/                     # 运维脚本
│   ├── desk_guard.py            # Desk :8000 守护进程
│   ├── install-desk-guard.sh    # 安装 macOS LaunchAgent
│   ├── stop-bench.sh            # 停止 bench 进程
│   └── fix-desk.sh              # 修复 + 后台重启
├── doc/                         # 业务文档与报告
│   ├── 10 样板间（制造行业）.md
│   ├── 系统升级注意事项.md
│   ├── erpnext-er-diagram.html
│   └── showroom-verification-report.md
├── openspec/                    # OpenSpec 变更管理
│
└── frappe-bench/                # ← 本仓库
    ├── apps/                    # Frappe 应用源码
    ├── sites/                   # 站点配置与资源
    │   ├── common_site_config.json
    │   └── west.bosofts.com/
    ├── config/                  # Redis 等进程配置
    ├── scripts/                 # Bench 内工具脚本
    │   ├── showroom/            # 制造样板间（见下文）
    │   ├── generate_er_diagram.py
    │   └── apply_chinese_coa.py
    ├── env/                     # Python 虚拟环境（gitignore）
    ├── logs/                    # 运行日志（gitignore）
    └── Procfile                 # honcho 进程定义
```

---

## 环境要求

- macOS（已针对 Homebrew / LaunchAgent 优化）
- MariaDB 或 MySQL 已运行
- Redis（`bench start` 会通过 Procfile 自动拉起）
- [bench CLI](https://frappeframework.com/docs/user/en/bench)（含 honcho）
- Node.js + Yarn（前端资源构建）

---

## 快速开始

### 1. 启动服务

在工作区根目录执行（**不要**直接在 bench 内 `bench start`，除非熟悉端口映射）：

```bash
cd ..   # 到工作区根目录（含 start.sh）
./start.sh
```

常用选项：

```bash
./start.sh --background          # 后台启动
./start.sh --repair              # migrate + 重建资源 + 清缓存后启动
./start.sh --repair --background
```

启动后访问：

| 地址 | 说明 |
|------|------|
| http://localhost:8000/desk/ | Desk 界面（desk-guard 代理） |
| http://localhost:18000 | Bench 内部 Web（API / 调试） |

默认登录：`Administrator` / 站点管理员密码。

### 2. 停止服务

```bash
../scripts/stop-bench.sh
```

### 3. Desk 异常修复

样式丢失、迁移后报错等情况：

```bash
../scripts/fix-desk.sh
```

或在 bench 目录手动：

```bash
bench --site west.bosofts.com migrate
bench build
bench --site west.bosofts.com clear-cache
```

浏览器 **Cmd+Shift+R** 硬刷新。

---

## AI 助手配置

Desk 右侧 AI 面板通过 iframe 加载外部 Agent。地址由 `ai_assistant_embed_url` 控制，优先级：

1. `sites/west.bosofts.com/site_config.json`（本地推荐，已 gitignore）
2. `sites/common_site_config.json`
3. `frappe_assistant_core` 代码默认值

**本地开发**示例（Agent 需在本机 4091 端口运行）：

```json
"ai_assistant_embed_url": "http://localhost:4091/agents/<agent-id>/<token>"
```

**生产环境**使用 `https://ai.bosofts.com/agents/...`。

修改后：

```bash
bench --site west.bosofts.com clear-cache
bench build --app frappe_assistant_core
bench restart
```

详细说明见 [`../doc/系统升级注意事项.md`](../doc/系统升级注意事项.md)。

MCP 对接与 FAC 管理界面：**Desk → FAC Admin**。应用文档见 [`apps/frappe_assistant_core/README.md`](apps/frappe_assistant_core/README.md)。

---

## 制造行业样板间

基于 [`../doc/10 样板间（制造行业）.md`](../doc/10 样板间（制造行业）.md)，通过脚本导入 **智联电脑组装有限公司** 的科目、主数据与完整业务流程（销售 → 采购 → 委外 → 生产 → 交付 → 收款），**不修改** `apps/` 源码。

```bash
cd frappe-bench

# 全流程
chmod +x scripts/showroom/run_all.sh
./scripts/showroom/run_all.sh all

# 分步：coa | settings | masters | flow | verify
./scripts/showroom/run_all.sh coa
```

验证报告输出：`../doc/showroom-verification-report.md`

详细用法见 [`scripts/showroom/README.md`](scripts/showroom/README.md)。

---

## 工具脚本

| 脚本 | 说明 |
|------|------|
| `scripts/generate_er_diagram.py` | 从 DocType 元数据生成交互式 E-R 图 HTML → `../doc/erpnext-er-diagram.html` |
| `scripts/apply_chinese_coa.py` | 应用中国会计准则科目表 |
| `scripts/showroom/` | 制造样板间数据与验证（见上） |

生成 E-R 图：

```bash
./env/bin/python scripts/generate_er_diagram.py
```

---

## 常用 Bench 命令

在 `frappe-bench/` 目录下，先激活虚拟环境：

```bash
source env/bin/activate
```

| 命令 | 说明 |
|------|------|
| `bench --site west.bosofts.com console` | Python 交互控制台 |
| `bench --site west.bosofts.com migrate` | 数据库迁移 |
| `bench build` | 构建全部前端资源 |
| `bench build --app frappe_assistant_core` | 仅构建指定应用 |
| `bench --site west.bosofts.com clear-cache` | 清站点缓存 |
| `bench --site west.bosofts.com backup` | 备份站点 |

---

## 进程与端口

`Procfile` 定义 honcho 管理的进程：

| 进程 | 端口 / 说明 |
|------|-------------|
| `web` | 18000 — Gunicorn |
| `socketio` | 9000 |
| `redis_cache` / `redis_queue` | 6379 |
| `worker` | 后台任务 |
| `schedule` | 定时任务 |
| `watch` | 前端热重载 |

Desk 对外 **8000** 由上层 `desk_guard.py` 代理到 18000，并支持按需自动启动 bench。

---

## 升级与维护

`git pull` 或版本升级后建议：

1. `bench --site west.bosofts.com migrate`
2. `bench build` 或 `../start.sh --repair`
3. `bench --site west.bosofts.com clear-cache`
4. 核对 AI 助手 URL 是否符合当前环境
5. 浏览器硬刷新

完整清单见 [`../doc/系统升级注意事项.md`](../doc/系统升级注意事项.md)。

---

## 环境变量

`start.sh` 支持以下变量（可选）：

| 变量 | 默认 | 说明 |
|------|------|------|
| `FRAPPE_SITE` | `west.bosofts.com` | 目标站点 |
| `FRAPPE_PUBLIC_PORT` | `8000` | Desk 代理端口 |
| `FRAPPE_BENCH_PORT` | `18000` | Bench Web 端口 |
| `FRAPPE_MYSQL_SOCKET` | `/tmp/mysql.sock` | MariaDB socket |
| `FRAPPE_SKIP_ASSET_PREP` | — | 跳过资源构建与缓存清理 |
| `FRAPPE_FORCE_BUILD` | — | 强制 `bench build` |
| `FRAPPE_SKIP_DESK_GUARD` | — | 不启动 desk guard |

---

## 相关文档

- [制造样板间业务文档](../doc/10%20样板间（制造行业）.md)
- [系统升级注意事项](../doc/系统升级注意事项.md)
- [样板间脚本说明](scripts/showroom/README.md)
- [Frappe Assistant Core](apps/frappe_assistant_core/README.md)
- [ERPNext 官方文档](https://docs.erpnext.com/)
- [Frappe Framework 文档](https://frappeframework.com/docs)

---

## 开发约定

- 自定义业务逻辑优先放在独立 Frappe 应用，避免直接改 `frappe` / `erpnext` 上游
- Schema 变更后执行 `migrate` + `build` + `clear-cache`
- OpenSpec 变更管理在工作区 `../openspec/`，分支命名 `feature/<change-name>`
