"""
数据模型定义
定义应用中使用的所有数据结构
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


# 科目类型常量
ACCOUNT_TYPE_ASSET = "资产"
ACCOUNT_TYPE_LIABILITY = "负债"
ACCOUNT_TYPE_EQUITY = "所有者权益"
ACCOUNT_TYPE_REVENUE = "收入"
ACCOUNT_TYPE_EXPENSE = "费用"

ACCOUNT_TYPES = [
    ACCOUNT_TYPE_ASSET,
    ACCOUNT_TYPE_LIABILITY,
    ACCOUNT_TYPE_EQUITY,
    ACCOUNT_TYPE_REVENUE,
    ACCOUNT_TYPE_EXPENSE,
]

# 报表类型常量
REPORT_TYPE_BALANCE_SHEET = "资产负债表"
REPORT_TYPE_INCOME_STATEMENT = "利润表"
REPORT_TYPE_CASH_FLOW = "现金流量表"
REPORT_TYPE_EQUITY_CHANGE = "所有者权益变动表"

REPORT_TYPES = [
    REPORT_TYPE_BALANCE_SHEET,
    REPORT_TYPE_INCOME_STATEMENT,
    REPORT_TYPE_CASH_FLOW,
    REPORT_TYPE_EQUITY_CHANGE,
]


@dataclass
class Account:
    """科目表 - 会计科目定义"""
    account_code: str       # 科目编码
    account_name: str       # 科目名称
    account_type: str       # 科目类型（资产/负债/所有者权益/收入/费用）
    parent_code: Optional[str] = None  # 父科目编码
    balance_direction: str = "借"      # 余额方向（借/贷）


@dataclass
class GeneralLedgerEntry:
    """序时账 - 会计分录"""
    id: int                    # 唯一标识
    entry_date: date           # 会计日期
    voucher_no: str            # 分录号
    account_code: str          # 科目编码
    account_name: str          # 科目名称
    debit_amount: Decimal      # 借方金额
    credit_amount: Decimal     # 贷方金额
    summary: str = ""          # 摘要
    user_id: int = 1           # 用户ID


@dataclass
class TrialBalanceEntry:
    """科目余额表 - 每个科目每期的汇总"""
    account_code: str          # 科目编码
    account_name: str          # 科目名称
    period: str                # 会计期间（如 2024-05）
    begin_balance: Decimal = Decimal("0")   # 期初余额
    debit_total: Decimal = Decimal("0")     # 借方发生额合计
    credit_total: Decimal = Decimal("0")    # 贷方发生额合计
    end_balance: Decimal = Decimal("0")     # 期末余额


@dataclass
class ReportItem:
    """会计报表项目"""
    item: str                  # 报表项目名称
    period: str                # 会计期间
    amount: Decimal = Decimal("0")  # 汇总金额
    report_type: str = ""      # 报表类型
