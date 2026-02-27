"""
数据管理工具
负责CSV文件的读写操作，管理所有数据的持久化存储
"""

import os
import pandas as pd
from typing import Optional

# 数据文件目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

# 数据文件路径常量
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.csv")
GENERAL_LEDGER_FILE = os.path.join(DATA_DIR, "general_ledger.csv")
TRIAL_BALANCE_FILE = os.path.join(DATA_DIR, "trial_balance.csv")
REPORT_FILE = os.path.join(DATA_DIR, "report.csv")


def ensureDataDir() -> None:
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)


def loadAccounts() -> pd.DataFrame:
    """加载科目表数据"""
    ensureDataDir()
    if os.path.exists(ACCOUNTS_FILE):
        return pd.read_csv(ACCOUNTS_FILE, dtype=str)
    return _createDefaultAccounts()


def saveAccounts(df: pd.DataFrame) -> None:
    """保存科目表数据"""
    ensureDataDir()
    df.to_csv(ACCOUNTS_FILE, index=False)


def loadGeneralLedger() -> pd.DataFrame:
    """加载序时账数据"""
    ensureDataDir()
    if os.path.exists(GENERAL_LEDGER_FILE):
        df = pd.read_csv(GENERAL_LEDGER_FILE)
        df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
        df["debit_amount"] = pd.to_numeric(df["debit_amount"], errors="coerce").fillna(0)
        df["credit_amount"] = pd.to_numeric(df["credit_amount"], errors="coerce").fillna(0)
        return df
    return pd.DataFrame(columns=[
        "id", "entry_date", "voucher_no", "account_code",
        "account_name", "debit_amount", "credit_amount", "summary", "user_id"
    ])


def saveGeneralLedger(df: pd.DataFrame) -> None:
    """保存序时账数据"""
    ensureDataDir()
    df.to_csv(GENERAL_LEDGER_FILE, index=False)


def loadTrialBalance() -> pd.DataFrame:
    """加载科目余额表数据"""
    ensureDataDir()
    if os.path.exists(TRIAL_BALANCE_FILE):
        return pd.read_csv(TRIAL_BALANCE_FILE)
    return pd.DataFrame(columns=[
        "account_code", "account_name", "period",
        "begin_balance", "debit_total", "credit_total", "end_balance"
    ])


def saveTrialBalance(df: pd.DataFrame) -> None:
    """保存科目余额表数据"""
    ensureDataDir()
    df.to_csv(TRIAL_BALANCE_FILE, index=False)


def loadReport() -> pd.DataFrame:
    """加载会计报表数据"""
    ensureDataDir()
    if os.path.exists(REPORT_FILE):
        return pd.read_csv(REPORT_FILE)
    return pd.DataFrame(columns=["item", "period", "amount", "report_type"])


def saveReport(df: pd.DataFrame) -> None:
    """保存会计报表数据"""
    ensureDataDir()
    df.to_csv(REPORT_FILE, index=False)


def _createDefaultAccounts() -> pd.DataFrame:
    """创建默认科目表"""
    default_accounts = [
        # 资产类
        {"account_code": "1001", "account_name": "现金", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        {"account_code": "1002", "account_name": "银行存款", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        {"account_code": "1101", "account_name": "短期投资", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        {"account_code": "1201", "account_name": "应收账款", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        {"account_code": "1501", "account_name": "固定资产", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        {"account_code": "1601", "account_name": "长期投资", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        # 负债类
        {"account_code": "2001", "account_name": "短期借款", "account_type": "负债", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "2201", "account_name": "应付账款", "account_type": "负债", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "2501", "account_name": "长期借款", "account_type": "负债", "parent_code": "", "balance_direction": "贷"},
        # 所有者权益类
        {"account_code": "3001", "account_name": "实收资本", "account_type": "所有者权益", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "3101", "account_name": "资本公积", "account_type": "所有者权益", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "3201", "account_name": "留存收益", "account_type": "所有者权益", "parent_code": "", "balance_direction": "贷"},
        # 收入类
        {"account_code": "4001", "account_name": "工资收入", "account_type": "收入", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "4101", "account_name": "投资收益", "account_type": "收入", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "4201", "account_name": "其他收入", "account_type": "收入", "parent_code": "", "balance_direction": "贷"},
        # 费用类
        {"account_code": "5001", "account_name": "生活费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
        {"account_code": "5101", "account_name": "交通费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
        {"account_code": "5201", "account_name": "娱乐费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
        {"account_code": "5301", "account_name": "教育费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
        {"account_code": "5401", "account_name": "医疗费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
        {"account_code": "5501", "account_name": "其他费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
    ]
    df = pd.DataFrame(default_accounts)
    saveAccounts(df)
    return df
