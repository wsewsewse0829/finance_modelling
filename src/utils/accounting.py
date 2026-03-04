"""
会计计算工具
负责序时账校验、科目余额表生成、会计报表生成等核心会计逻辑
"""

import pandas as pd
import numpy as np
from typing import Tuple, List


def validateJournalEntries(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    校验序时账借贷是否平衡
    返回: (是否平衡, 错误信息列表)
    """
    errors = []

    if df.empty:
        return True, []

    # 按分录号分组校验每笔分录借贷是否平衡
    grouped = df.groupby("voucher_no")
    for voucher_no, group in grouped:
        debit_sum = group["debit_amount"].sum()
        credit_sum = group["credit_amount"].sum()
        if abs(debit_sum - credit_sum) > 0.01:
            errors.append(
                f"分录 {voucher_no}: 借方合计 {debit_sum:.2f} ≠ 贷方合计 {credit_sum:.2f}"
            )

    is_balanced = len(errors) == 0
    return is_balanced, errors


def generateTrialBalance(
    general_ledger: pd.DataFrame,
    accounts: pd.DataFrame
) -> pd.DataFrame:
    """
    根据序时账生成科目余额表
    实现连续编报：本期期初余额 = 上期期末余额
    对于没有业务的科目，余额也会延续到后续期间
    """
    if general_ledger.empty:
        return pd.DataFrame(columns=[
            "account_code", "account_name", "period",
            "begin_balance", "debit_total", "credit_total", "end_balance"
        ])

    # 添加期间列
    gl = general_ledger.copy()
    # 转换日期为datetime并提取期间（使用errors="coerce"处理无效日期）
    gl["period"] = pd.to_datetime(gl["entry_date"], errors="coerce").dt.strftime("%Y-%m")
    # 过滤掉日期转换失败的记录
    gl = gl[gl["period"].notna() & (gl["period"] != "")]

    # 确保科目编码为字符串类型
    gl["account_code"] = gl["account_code"].astype(str)
    accounts_str = accounts.copy()
    accounts_str["account_code"] = accounts_str["account_code"].astype(str)

    # 按科目和期间汇总业务发生额
    summary = gl.groupby(["account_code", "period"]).agg(
        debit_total=("debit_amount", "sum"),
        credit_total=("credit_amount", "sum"),
    ).reset_index()

    # 获取科目余额方向和名称
    account_info = accounts_str.set_index("account_code")[["account_name", "balance_direction"]].to_dict("index")

    # 获取所有期间并按时间排序
    # 必须从原始序时账中提取所有期间，而不是从汇总数据中
    periods = sorted(gl["period"].unique())
    
    # 获取所有科目（包括科目表中定义的所有科目）
    all_accounts = accounts_str[["account_code", "account_name"]].to_dict("records")
    
    # 记录每个科目的上期期末余额
    account_end_balance = {}
    
    # 初始化所有科目的上期期末余额为0
    for account in all_accounts:
        account_end_balance[account["account_code"]] = 0.0
    
    # 对每个科目按时间顺序计算期初和期末余额
    result_rows = []
    
    for period in periods:
        # 获取当前期间的业务数据
        period_summary = summary[summary["period"] == period].set_index("account_code")
        
        # 处理每个科目
        for account in all_accounts:
            account_code = account["account_code"]
            account_name = account["account_name"]
            balance_direction = account_info.get(account_code, {}).get("balance_direction", "借")
            
            # 获取本期发生额（如果没有业务，则为0）
            if account_code in period_summary.index:
                debit_total = period_summary.loc[account_code, "debit_total"]
                credit_total = period_summary.loc[account_code, "credit_total"]
            else:
                debit_total = 0.0
                credit_total = 0.0
            
            # 期初余额 = 上期期末余额（如果没有上期，则为0）
            begin_balance = account_end_balance.get(account_code, 0.0)
            
            # 计算期末余额
            end_balance = _calculateEndBalance(
                begin_balance,
                debit_total,
                credit_total,
                balance_direction
            )
            
            # 保存期末余额供下期使用
            account_end_balance[account_code] = end_balance
            
            # 只有当科目有余额或有业务时才添加到结果中
            if abs(begin_balance) > 0.01 or abs(debit_total) > 0.01 or abs(credit_total) > 0.01 or abs(end_balance) > 0.01:
                result_rows.append({
                    "account_code": account_code,
                    "account_name": account_name,
                    "period": period,
                    "begin_balance": begin_balance,
                    "debit_total": debit_total,
                    "credit_total": credit_total,
                    "end_balance": end_balance
                })
    
    result_df = pd.DataFrame(result_rows)
    
    return result_df[["account_code", "account_name", "period",
                     "begin_balance", "debit_total", "credit_total", "end_balance"]]


def generateReport(
    trial_balance: pd.DataFrame,
    accounts: pd.DataFrame
) -> pd.DataFrame:
    """
    根据科目余额表生成会计报表
    """
    if trial_balance.empty:
        return pd.DataFrame(columns=["item", "period", "amount", "report_type"])

    reports = []

    # 确保科目编码为字符串类型，避免合并时类型不匹配
    tb_temp = trial_balance.copy()
    tb_temp["account_code"] = tb_temp["account_code"].astype(str)
    accounts_temp = accounts.copy()
    accounts_temp["account_code"] = accounts_temp["account_code"].astype(str)

    # 合并科目类型信息
    tb = tb_temp.merge(
        accounts_temp[["account_code", "account_type"]],
        on="account_code",
        how="left"
    )

    periods = tb["period"].unique()

    for period in periods:
        period_data = tb[tb["period"] == period]

        # 资产负债表
        asset_total = period_data[period_data["account_type"] == "资产"]["end_balance"].sum()
        liability_total = period_data[period_data["account_type"] == "负债"]["end_balance"].sum()
        
        # 所有者权益包括：
        # 1. 所有者权益类科目的期末余额
        # 2. 净利润（收入贷方发生额 - 费用借方发生额）
        equity_accounts_total = period_data[period_data["account_type"] == "所有者权益"]["end_balance"].sum()
        revenue_credit_total = period_data[period_data["account_type"] == "收入"]["credit_total"].sum()
        expense_debit_total = period_data[period_data["account_type"] == "费用"]["debit_total"].sum()
        net_income = revenue_credit_total - expense_debit_total
        
        # 所有者权益总计 = 所有者权益类科目 + 净利润
        equity_total = equity_accounts_total + net_income

        reports.append({"item": "资产总计", "period": period, "amount": asset_total, "report_type": "资产负债表"})
        reports.append({"item": "负债总计", "period": period, "amount": liability_total, "report_type": "资产负债表"})
        reports.append({"item": "所有者权益总计", "period": period, "amount": equity_total, "report_type": "资产负债表"})

        # 利润表
        reports.append({"item": "收入合计", "period": period, "amount": revenue_credit_total, "report_type": "利润表"})
        reports.append({"item": "费用合计", "period": period, "amount": expense_debit_total, "report_type": "利润表"})
        reports.append({"item": "净利润", "period": period, "amount": net_income, "report_type": "利润表"})

    return pd.DataFrame(reports)


def validateReport(report: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    校验会计报表是否平衡
    资产 = 负债 + 所有者权益
    """
    errors = []

    if report.empty:
        return True, []

    bs = report[report["report_type"] == "资产负债表"]
    periods = bs["period"].unique()

    for period in periods:
        period_data = bs[bs["period"] == period]
        asset = period_data[period_data["item"] == "资产总计"]["amount"].sum()
        liability = period_data[period_data["item"] == "负债总计"]["amount"].sum()
        equity = period_data[period_data["item"] == "所有者权益总计"]["amount"].sum()

        if abs(asset - liability - equity) > 0.01:
            errors.append(
                f"期间 {period}: 资产({asset:.2f}) ≠ 负债({liability:.2f}) + 所有者权益({equity:.2f})"
            )

    is_balanced = len(errors) == 0
    return is_balanced, errors


def _calculateEndBalance(
    begin_balance: float,
    debit_total: float,
    credit_total: float,
    balance_direction: str
) -> float:
    """计算期末余额"""
    if balance_direction == "借":
        return begin_balance + debit_total - credit_total
    else:
        return begin_balance - debit_total + credit_total
