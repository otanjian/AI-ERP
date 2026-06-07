# 制造行业样板间验证报告

- 公司：智联电脑组装有限公司
- 生成时间：2026-06-06T16:46:41
- 汇总：**16 Pass / 2 Fail**（共 18 项）

## 测试验证清单

| 模块 | 测试项 | 预期 | 实际 | 状态 |
| --- | --- | --- | --- | --- |
| 库存 | CPU ITEM-002 WH-RAW01 | 50 | 0.0 | Fail |
| 库存 | 主板 ITEM-003 WH-RAW01 | 50 | 0.0 | Fail |
| 库存 | 成品 ITEM-001 WH-FG01 | 0 | 0.0 | Pass |
| 销售 | SO qty ITEM-001 | 50 | 50.0 | Pass |
| 生产 | WO qty | 50 | 50.0 | Pass |
| 销售 | DN qty ITEM-001 | 50 | 50.0 | Pass |
| 财务 | SI grand_total | 197750 | 197750.0 | Pass |
| 财务 | SI net_total | 175000 | 175000.0 | Pass |
| 财务 | SI outstanding after payment | 0 | 0.0 | Pass |
| 财务 | PI SUPP-001 grand_total | 85880 | 85880.0 | Pass |
| 财务 | PI SUPP-001 outstanding | 0 | 0.0 | Pass |
| MRP | MR net ITEM-002 | 40 | 40.0 | Pass |
| MRP | MR net ITEM-003 | 35 | 35.0 | Pass |
| MRP | MR net ITEM-004 | 70 | 70.0 | Pass |
| MRP | MR net ITEM-005 | 30 | 30.0 | Pass |
| MRP | MR net ITEM-006 | 25 | 25.0 | Pass |
| MRP | MR net ITEM-007 | 10 | 10.0 | Pass |
| MRP | MR net ITEM-008 | 50 | 50.0 | Pass |

## 文档对照 §6

| 流程模块 | 状态 |
| --- | --- |
| 基础档案 | 部分 |
| 销售流程 | Pass |
| 采购流程 | Pass |
| 生产流程 | Pass |
| 数据一致性 | Fail |
