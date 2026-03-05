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
        
        # 所有者权益 = 所有者权益类科目的期末余额
        # 注意：收入和费用科目的余额已通过期末余额反映在所有者权益中
        equity_total = period_data[period_data["account_type"] == "所有者权益"]["end_balance"].sum()

        reports.append({"item": "资产总计", "period": period, "amount": asset_total, "report_type": "资产负债表"})
        reports.append({"item": "负债总计", "period": period, "amount": liability_total, "report_type": "资产负债表"})
        reports.append({"item": "所有者权益总计", "period": period, "amount": equity_total, "report_type": "资产负债表"})

        # 利润表
        revenue_credit_total = period_data[period_data["account_type"] == "收入"]["credit_total"].sum()
        expense_debit_total = period_data[period_data["account_type"] == "费用"]["debit_total"].sum()
        net_income = revenue_credit_total - expense_debit_total
        
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

        if abs(asset - liability - equity) > 1:
            errors.append(
                f"期间 {period}: 资产({asset:.2f}) ≠ 负债({liability:.2f}) + 所有者权益({equity:.2f})"
            )

    is_balanced = len(errors) == 0
    return is_balanced, errors


def generateClosingStep1(
    entries: pd.DataFrame,
    accounts: pd.DataFrame,
    actual_budget: str,
    period: str,
    date: str,
    summary: str = "结转本期利润"
) -> pd.DataFrame:
    """
    第一步结转：收入/费用 → 本年利润
    支持多科目结转
    
    Args:
        entries: 分录数据（包含 account_code, debit_amount, credit_amount, account_type）
        accounts: 科目表
        actual_budget: 数据类型（"实际"或"预算"）
        period: 会计期间
        date: 凭证日期
        summary: 分录摘要
        
    Returns:
        pd.DataFrame: 结转分录数据
    """
    import pandas as pd
    from datetime import datetime
    
    # 合并科目类型信息
    accounts_temp = accounts.copy()
    accounts_temp["account_code"] = accounts_temp["account_code"].astype(str)
    entries_temp = entries.copy()
    entries_temp["account_code"] = entries_temp["account_code"].astype(str)
    
    entries_with_type = entries_temp.merge(
        accounts_temp[["account_code", "account_name", "account_type"]],
        on="account_code",
        how="left"
    )
    
    closing_entries = []
    
    # 获取下一个凭证号
    voucher_no = _generateNextVoucherNo(period, date)
    
    # 处理收入类科目
    revenue_entries = entries_with_type[entries_with_type["account_type"] == "收入"]
    if not revenue_entries.empty:
        for _, row in revenue_entries.iterrows():
            if row["credit_amount"] > 0:
                # 借：本年利润，贷：收入科目
                closing_entries.append({
                    "entry_date": date,
                    "voucher_no": voucher_no,
                    "account_code": "3103",  # 本年利润
                    "account_name": "本年利润",
                    "debit_amount": row["credit_amount"],
                    "credit_amount": 0,
                    "summary": summary,
                    "actual_budget": actual_budget
                })
    
    # 处理费用类科目
    expense_entries = entries_with_type[entries_with_type["account_type"] == "费用"]
    if not expense_entries.empty:
        for _, row in expense_entries.iterrows():
            if row["debit_amount"] > 0:
                # 借：费用科目，贷：本年利润
                closing_entries.append({
                    "entry_date": date,
                    "voucher_no": voucher_no,
                    "account_code": row["account_code"],
                    "account_name": row["account_name"],
                    "debit_amount": 0,
                    "credit_amount": row["debit_amount"],
                    "summary": summary,
                    "actual_budget": actual_budget
                })
    
    # 如果没有需要结转的科目，返回空数据框
    if not closing_entries:
        return pd.DataFrame()
    
    # 计算本年利润的总借方和总贷方
    closing_df = pd.DataFrame(closing_entries)
    
    # 确保本年利润科目有贷方余额（净利润）或借方余额（净亏损）
    total_revenue_closing = closing_df[closing_df["account_code"] == "3103"]["debit_amount"].sum()
    total_expense_closing = closing_df[closing_df["account_code"] != "3103"]["credit_amount"].sum()
    net_income = total_revenue_closing - total_expense_closing
    
    if net_income > 0:  # 净利润，本年利润有贷方余额
        closing_df.loc[closing_df["account_code"] == "3103", "credit_amount"] = net_income
    elif net_income < 0:  # 净亏损，本年利润有借方余额
        closing_df.loc[closing_df["account_code"] == "3103", "debit_amount"] = abs(net_income)
    
    return closing_df[["entry_date", "voucher_no", "account_code", "account_name", 
                   "debit_amount", "credit_amount", "summary", "actual_budget"]]


def generateClosingStep2(
    step1_entries: pd.DataFrame,
    actual_budget: str,
    period: str,
    date: str,
    summary: str = "结转至留存收益"
) -> pd.DataFrame:
    """
    第二步结转：本年利润 → 留存收益
    
    Args:
        step1_entries: 第一步结转的分录数据
        actual_budget: 数据类型（"实际"或"预算"）
        period: 会计期间
        date: 凭证日期
        summary: 分录摘要
        
    Returns:
        pd.DataFrame: 结转分录数据
    """
    import pandas as pd
    
    # 计算本年利润的余额
    profit_df = step1_entries[step1_entries["account_code"] == "3103"]
    if profit_df.empty:
        return pd.DataFrame()
    
    debit_total = profit_df["debit_amount"].sum()
    credit_total = profit_df["credit_amount"].sum()
    net_income = credit_total - debit_total
    
    # 如果净利润为0，不需要结转
    if abs(net_income) < 0.01:
        return pd.DataFrame()
    
    # 获取下一个凭证号
    voucher_no = _generateNextVoucherNo(period, date)
    
    # 生成结转分录
    if net_income > 0:  # 净利润
        closing_entries = [
            {
                "entry_date": date,
                "voucher_no": voucher_no,
                "account_code": "3103",  # 本年利润
                "account_name": "本年利润",
                "debit_amount": net_income,
                "credit_amount": 0,
                "summary": summary,
                "actual_budget": actual_budget
            },
            {
                "entry_date": date,
                "voucher_no": voucher_no,
                "account_code": "3201",  # 留存收益
                "account_name": "留存收益",
                "debit_amount": 0,
                "credit_amount": net_income,
                "summary": summary,
                "actual_budget": actual_budget
            }
        ]
    else:  # 净亏损
        closing_entries = [
            {
                "entry_date": date,
                "voucher_no": voucher_no,
                "account_code": "3201",  # 留存收益
                "account_name": "留存收益",
                "debit_amount": abs(net_income),
                "credit_amount": 0,
                "summary": summary,
                "actual_budget": actual_budget
            },
            {
                "entry_date": date,
                "voucher_no": voucher_no,
                "account_code": "3103",  # 本年利润
                "account_name": "本年利润",
                "debit_amount": 0,
                "credit_amount": abs(net_income),
                "summary": summary,
                "actual_budget": actual_budget
            }
        ]
    
    df = pd.DataFrame(closing_entries)
    return df[["entry_date", "voucher_no", "account_code", "account_name", 
               "debit_amount", "credit_amount", "summary", "actual_budget"]]


def _generateNextVoucherNo(period: str, date: str) -> str:
    """
    生成下一个凭证号
    格式：YYYY-MM-XXX
    
    Args:
        period: 会计期间（如 2024-03）
        date: 凭证日期（如 2024-03-15）
        
    Returns:
        str: 凭证号
    """
    # 简单实现：使用日期作为基础
    # 在实际应用中，应该查询数据库获取当前期间的最大凭证号
    return f"{period}-001"


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

