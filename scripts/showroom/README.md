# 制造行业样板间 — ERPNext 数据与配置脚本

基于 `doc/10 样板间（制造行业）.md`，在 **不修改** `frappe-bench/apps/` 程序代码的前提下，通过 bench 脚本完成科目、主数据、业务流程与验证。

## 前提

- Bench 已启动，站点默认：`west.bosofts.com`
- 公司：**智联电脑组装有限公司**（已存在则复用）
- 执行目录：`frappe-bench/`

## 快速运行

```bash
cd frappe-bench

# 可选：备份
./scripts/showroom/run_all.sh backup

# 全流程（科目 → 设置 → 主数据 → 业务流 → 验证）
chmod +x scripts/showroom/run_all.sh
./scripts/showroom/run_all.sh all
```

分步执行：

```bash
./scripts/showroom/run_all.sh coa       # 科目与 13% 增值税模板
./scripts/showroom/run_all.sh settings # 库存/采购/销售/生产设置
./scripts/showroom/run_all.sh masters  # 仓库、物料、BOM、期初库存
./scripts/showroom/run_all.sh flow     # 销售→采购→委外→生产→交付→收款
./scripts/showroom/run_all.sh verify   # 生成验证报告
```

也可直接调用 CLI：

```bash
./env/bin/python scripts/showroom/cli.py setup_coa
```

## 目录结构

```
scripts/showroom/
├── config.yaml          # 站点、公司、过账日期
├── fixtures/            # JSON 主数据
├── setup_coa.py         # 中国准则科目扩展 + 税模板
├── setup_settings.py    # ERPNext 模块设置
├── setup_masters.py     # 主数据加载
├── run_flow.py          # 业务流程
├── verify.py            # 断言与报告
├── cli.py               # bench 上下文入口（run_all.sh 调用）
├── showroom_state.json  # 运行后生成的单据 ID（自动生成）
└── run_all.sh
```

## 验证报告

运行 `verify` 后输出：`doc/showroom-verification-report.md`

## 回滚

1. 使用 `bench --site west.bosofts.com backup` 的备份恢复；或
2. 在 Desk 中取消提交并删除 **智联电脑组装有限公司** 下的演示单据（不影响其他公司）。

## 约束

- **禁止**修改 `frappe-bench/apps/` 下任何应用源码
- 仅通过标准 DocType API、fixtures 与系统设置完成配置
- 不要求 `bench migrate` / `bench build`
