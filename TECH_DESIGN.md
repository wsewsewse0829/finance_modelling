# 财务模型应用技术设计

## 技术栈
- 后端/功能层：Python
- 前段/交互层：Streamlit
- 数据处理：Pandas/Numpy
- 存储方式：csv文件
- 可视化：Matplotlib/Plotly
- 文档管理：Markdown
- 云端部署：Steamlit Cloud

## 项目结构

src/
  components/  #组建
  pages/       #页面
  hooks/       #自定义Hooks
  utils/       #工具函数
  types/       #类型定义

## 数据模型

### 序时账(General Ledger)
- id: int  # 唯一标识
- date: date  # 会计期间
- voucher_no: varchar  # 分录号
- account_code: varchar  # 科目编码
- account_name: varchar  # 科目名称
- debit_amount: decimal  # 借方金额
- credit_amount: decimal  # 贷方金额
- summary: varchar  # 摘要
- user_id: int  # 用户ID

### 科目余额表（Trial Balance）
根据序时账汇总生成，记录每个科目在每月（或期间）的期初余额、本期借/贷发生额、期末余额。
- account_code: varchar  # 科目编码
- period: varchar  # 会计期间（如2024-05）
- begin_balance # 期初余额
- debit_total: decimal  # 借方金额合计
- credit_total: decimal  # 贷方金额合计
- end_balance # 期末余额

### 会计报表（Report:Balance Sheet and P&L）
- item: varchar  # 报表项目
- period: varchar  # 会计期间（如2024-05）
- amount: decimal  # 汇总金额

### 科目表（Account）
- account_code: varchar  # 科目编码
- account_name: varchar  # 科目名称
- account_type: varchar  # 科目类型（资产/负债/等）
- parent_code:  varchar  # 父科目编码

### 数据结构关系图（Mermaid示意）

erDiagram
    General Ledger ||--|| ACCOUNT : uses
    General Ledger }|..|{ Trial Balance : aggregating
    Trial Balance ||--|| ACCOUNT : belongs_to
    Trial Balance }|--|{ REPORT : summarizes


