"""
预实分析页面
对比实际数据和预算数据，分析差异
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils.data_manager import loadGeneralLedger, loadAccounts
from src.utils.accounting import generateTrialBalance


def renderBudgetAnalysisPage() -> None:
    """渲染预实分析页面"""
    st.title("📈 预实分析")
    st.markdown("---")

    # 加载数据
    ledger = loadGeneralLedger()
    accounts = loadAccounts()

    if ledger.empty:
        st.warning("暂无数据。请先在「数据上传」页面上传序时账数据。")
        _renderSampleView()
        return

    # 分离实际数据和预算数据
    actual_ledger = ledger[ledger["actual_budget"] == "实际"].copy()
    budget_ledger = ledger[ledger["actual_budget"] == "预算"].copy()

    if actual_ledger.empty and budget_ledger.empty:
        st.warning("暂无数据。请先上传实际数据和预算数据。")
        _renderSampleView()
        return

    # 生成实际数据和预算数据的科目余额表
    actual_tb = generateTrialBalance(actual_ledger, accounts) if not actual_ledger.empty else pd.DataFrame()
    budget_tb = generateTrialBalance(budget_ledger, accounts) if not budget_ledger.empty else pd.DataFrame()

    # 获取期间（合并实际和预算数据的期间）
    all_periods = set()
    if not actual_tb.empty:
        all_periods.update(actual_tb["period"].unique())
    if not budget_tb.empty:
        all_periods.update(budget_tb["period"].unique())

    periods = sorted(all_periods)

    if not periods:
        st.warning("暂无期间数据。")
        _renderSampleView()
        return

    # 期间选择
    selected_periods = st.multiselect(
        "选择会计期间",
        periods,
        default=periods[-3:] if len(periods) >= 3 else periods,
    )

    if not selected_periods:
        st.info("请选择至少一个会计期间。")
        return

    # 合并科目类型信息
    if not actual_tb.empty:
        actual_tb["account_code"] = actual_tb["account_code"].astype(str)
    if not budget_tb.empty:
        budget_tb["account_code"] = budget_tb["account_code"].astype(str)
    
    accounts_str = accounts.copy()
    accounts_str["account_code"] = accounts_str["account_code"].astype(str)

    # 报表展示标签页
    tab_bs, tab_pl, tab_chart, tab_detail = st.tabs([
        "资产负债表", "利润表", "可视化图表", "科目明细"
    ])

    with tab_bs:
        _renderBalanceSheetComparison(actual_tb, budget_tb, accounts_str, selected_periods)

    with tab_pl:
        _renderIncomeStatementComparison(actual_tb, budget_tb, accounts_str, selected_periods)

    with tab_chart:
        _renderBudgetComparisonCharts(actual_tb, budget_tb, accounts_str, selected_periods)

    with tab_detail:
        _renderBudgetAccountDetail(actual_tb, budget_tb, accounts_str, selected_periods)


def _renderBalanceSheetComparison(
    actual_tb: pd.DataFrame,
    budget_tb: pd.DataFrame,
    accounts: pd.DataFrame,
    periods: list
) -> None:
    """渲染资产负债表对比"""
    st.subheader("资产负债表")

    try:
        # 合并科目类型信息
        if not actual_tb.empty:
            actual_tb = actual_tb.merge(
                accounts[["account_code", "account_type", "account_name"]],
                on="account_code",
                how="left"
            )
        if not budget_tb.empty:
            budget_tb = budget_tb.merge(
                accounts[["account_code", "account_type", "account_name"]],
                on="account_code",
                how="left"
            )

        # 按科目类型分组
        account_types = ["资产", "负债", "所有者权益"]

        for account_type in account_types:
            st.markdown(f"#### {account_type}")

            try:
                # 获取实际数据和预算数据
                actual_pivot = pd.DataFrame()
                budget_pivot = pd.DataFrame()

                if not actual_tb.empty and "account_type" in actual_tb.columns:
                    actual_data = actual_tb[actual_tb["account_type"] == account_type].copy()
                    if not actual_data.empty and all(col in actual_data.columns for col in ["account_name", "period", "end_balance"]):
                        try:
                            actual_pivot = actual_data.pivot_table(
                                index="account_name",
                                columns="period",
                                values="end_balance",
                                aggfunc="sum"
                            )
                        except Exception as pivot_error:
                            st.warning(f"实际数据{account_type}透视表生成失败: {str(pivot_error)}")
                            actual_pivot = pd.DataFrame()

                if not budget_tb.empty and "account_type" in budget_tb.columns:
                    budget_data = budget_tb[budget_tb["account_type"] == account_type].copy()
                    if not budget_data.empty and all(col in budget_data.columns for col in ["account_name", "period", "end_balance"]):
                        try:
                            budget_pivot = budget_data.pivot_table(
                                index="account_name",
                                columns="period",
                                values="end_balance",
                                aggfunc="sum"
                            )
                        except Exception as pivot_error:
                            st.warning(f"预算数据{account_type}透视表生成失败: {str(pivot_error)}")
                            budget_pivot = pd.DataFrame()

                # 创建对比表
                try:
                    comparison_df = _createComparisonTable(
                        actual_pivot, budget_pivot, periods
                    )
                except Exception as comp_error:
                    st.warning(f"创建{account_type}对比表失败: {str(comp_error)}")
                    comparison_df = pd.DataFrame()

                if not comparison_df.empty:
                    st.dataframe(comparison_df.style.format({"实际": "{:.2f}", "预算": "{:.2f}", "预实差异": "{:.2f}"}), use_container_width=True)
                elif actual_pivot.empty and budget_pivot.empty:
                    st.info(f"暂无{account_type}数据。")
            except Exception as e:
                st.warning(f"生成{account_type}对比表时遇到问题，已跳过。错误详情: {str(e)}")
                continue

        # 显示汇总数据
        st.markdown("---")
        st.markdown("#### 汇总")

        summary_comparison = _createBalanceSheetSummary(actual_tb, budget_tb, periods)
        if not summary_comparison.empty:
            st.dataframe(summary_comparison.style.format({"实际": "{:.2f}", "预算": "{:.2f}", "预实差异": "{:.2f}"}), use_container_width=True)
    except Exception as e:
        st.error(f"资产负债表对比功能遇到错误: {str(e)}")
        st.info("请检查数据格式或联系管理员。")


def _createComparisonTable(
    actual_pivot: pd.DataFrame,
    budget_pivot: pd.DataFrame,
    periods: list
) -> pd.DataFrame:
    """创建对比表"""
    result_rows = []

    # 获取所有科目名称
    all_accounts = set()
    if not actual_pivot.empty:
        all_accounts.update(actual_pivot.index)
    if not budget_pivot.empty:
        all_accounts.update(budget_pivot.index)

    for period in periods:
        for account_name in sorted(all_accounts):
            # 获取实际值
            if not actual_pivot.empty and account_name in actual_pivot.index:
                actual_value = actual_pivot.loc[account_name, period] if period in actual_pivot.columns else 0
            else:
                actual_value = 0

            # 获取预算值
            if not budget_pivot.empty and account_name in budget_pivot.index:
                budget_value = budget_pivot.loc[account_name, period] if period in budget_pivot.columns else 0
            else:
                budget_value = 0

            # 计算差异
            difference = actual_value - budget_value

            result_rows.append({
                "科目名称": account_name,
                "期间": period,
                "实际": actual_value,
                "预算": budget_value,
                "预实差异": difference
            })

    df = pd.DataFrame(result_rows)
    if not df.empty:
        # 创建透视表
        df_pivot = df.pivot_table(
            index="科目名称",
            columns="期间",
            values=["实际", "预算", "预实差异"],
            aggfunc="first"
        )

        # 重新索引列
        result_df = pd.DataFrame(index=df_pivot.index)
        for period in periods:
            for value_type in ["实际", "预算", "预实差异"]:
                col_name = f"{value_type}_{period}"
                if col_name in df_pivot.columns:
                    result_df[(period, value_type)] = df_pivot[col_name]
                else:
                    result_df[(period, value_type)] = 0

        # 展开多级列
        result_df.columns = [f"{col[1]}_{col[0]}" if isinstance(col, tuple) else col for col in result_df.columns]

        return df.pivot_table(
            index="科目名称",
            columns="期间",
            values=["实际", "预算", "预实差异"],
            aggfunc="first"
        ).reindex(level=1, axis=1, columns=periods).swaplevel(axis=1)

    return pd.DataFrame()


def _createBalanceSheetSummary(
    actual_tb: pd.DataFrame,
    budget_tb: pd.DataFrame,
    periods: list
) -> pd.DataFrame:
    """创建资产负债表汇总"""
    summary_rows = []

    for period in periods:
        # 实际数据汇总
        if not actual_tb.empty:
            period_actual = actual_tb[actual_tb["period"] == period]
            asset_actual = period_actual[period_actual["account_type"] == "资产"]["end_balance"].sum()
            liability_actual = period_actual[period_actual["account_type"] == "负债"]["end_balance"].sum()
            equity_actual = period_actual[period_actual["account_type"] == "所有者权益"]["end_balance"].sum()
        else:
            asset_actual = 0
            liability_actual = 0
            equity_actual = 0

        # 预算数据汇总
        if not budget_tb.empty:
            period_budget = budget_tb[budget_tb["period"] == period]
            asset_budget = period_budget[period_budget["account_type"] == "资产"]["end_balance"].sum()
            liability_budget = period_budget[period_budget["account_type"] == "负债"]["end_balance"].sum()
            equity_budget = period_budget[period_budget["account_type"] == "所有者权益"]["end_balance"].sum()
        else:
            asset_budget = 0
            liability_budget = 0
            equity_budget = 0

        summary_rows.append({
            "科目名称": "资产总计",
            "期间": period,
            "实际": asset_actual,
            "预算": asset_budget,
            "预实差异": asset_actual - asset_budget
        })
        summary_rows.append({
            "科目名称": "负债总计",
            "期间": period,
            "实际": liability_actual,
            "预算": liability_budget,
            "预实差异": liability_actual - liability_budget
        })
        summary_rows.append({
            "科目名称": "所有者权益总计",
            "期间": period,
            "实际": equity_actual,
            "预算": equity_budget,
            "预实差异": equity_actual - equity_budget
        })

    df = pd.DataFrame(summary_rows)
    if not df.empty:
        df_pivot = df.pivot_table(
            index="科目名称",
            columns="期间",
            values=["实际", "预算", "预实差异"],
            aggfunc="first"
        )
        return df_pivot.reindex(["资产总计", "负债总计", "所有者权益总计"])

    return pd.DataFrame()


def _renderIncomeStatementComparison(
    actual_tb: pd.DataFrame,
    budget_tb: pd.DataFrame,
    accounts: pd.DataFrame,
    periods: list
) -> None:
    """渲染利润表对比"""
    st.subheader("利润表")

    try:
        # 合并科目类型信息
        if not actual_tb.empty:
            actual_tb = actual_tb.merge(
                accounts[["account_code", "account_type", "account_name"]],
                on="account_code",
                how="left"
            )
        if not budget_tb.empty:
            budget_tb = budget_tb.merge(
                accounts[["account_code", "account_type", "account_name"]],
                on="account_code",
                how="left"
            )

        # 按科目类型分组
        account_types = ["收入", "费用"]

        for account_type in account_types:
            st.markdown(f"#### {account_type}")

            try:
                # 确定使用的列
                value_column = "credit_total" if account_type == "收入" else "debit_total"

                # 获取实际数据和预算数据
                actual_pivot = pd.DataFrame()
                budget_pivot = pd.DataFrame()

                if not actual_tb.empty and "account_type" in actual_tb.columns:
                    actual_data = actual_tb[actual_tb["account_type"] == account_type].copy()
                    if not actual_data.empty and all(col in actual_data.columns for col in ["account_name", "period", value_column]):
                        try:
                            actual_pivot = actual_data.pivot_table(
                                index="account_name",
                                columns="period",
                                values=value_column,
                                aggfunc="sum"
                            )
                        except Exception as pivot_error:
                            st.warning(f"实际数据{account_type}透视表生成失败: {str(pivot_error)}")
                            actual_pivot = pd.DataFrame()

                if not budget_tb.empty and "account_type" in budget_tb.columns:
                    budget_data = budget_tb[budget_tb["account_type"] == account_type].copy()
                    if not budget_data.empty and all(col in budget_data.columns for col in ["account_name", "period", value_column]):
                        try:
                            budget_pivot = budget_data.pivot_table(
                                index="account_name",
                                columns="period",
                                values=value_column,
                                aggfunc="sum"
                            )
                        except Exception as pivot_error:
                            st.warning(f"预算数据{account_type}透视表生成失败: {str(pivot_error)}")
                            budget_pivot = pd.DataFrame()

                # 创建对比表
                try:
                    comparison_df = _createIncomeComparisonTable(
                        actual_pivot, budget_pivot, periods
                    )
                except Exception as comp_error:
                    st.warning(f"创建{account_type}对比表失败: {str(comp_error)}")
                    comparison_df = pd.DataFrame()

                if not comparison_df.empty:
                    st.dataframe(comparison_df.style.format({"实际": "{:.2f}", "预算": "{:.2f}", "预实差异": "{:.2f}"}), use_container_width=True)
                elif actual_pivot.empty and budget_pivot.empty:
                    st.info(f"暂无{account_type}数据。")
            except Exception as e:
                st.warning(f"生成{account_type}对比表时遇到问题，已跳过。错误详情: {str(e)}")
                continue

        # 显示汇总数据
        st.markdown("---")
        st.markdown("#### 汇总")

        summary_comparison = _createIncomeStatementSummary(actual_tb, budget_tb, periods)
        if not summary_comparison.empty:
            st.dataframe(summary_comparison.style.format({"实际": "{:.2f}", "预算": "{:.2f}", "预实差异": "{:.2f}"}), use_container_width=True)
    except Exception as e:
        st.error(f"利润表对比功能遇到错误: {str(e)}")
        st.info("请检查数据格式或联系管理员。")


def _createIncomeComparisonTable(
    actual_pivot: pd.DataFrame,
    budget_pivot: pd.DataFrame,
    periods: list
) -> pd.DataFrame:
    """创建利润表对比表"""
    result_rows = []

    # 获取所有科目名称
    all_accounts = set()
    if not actual_pivot.empty:
        all_accounts.update(actual_pivot.index)
    if not budget_pivot.empty:
        all_accounts.update(budget_pivot.index)

    for period in periods:
        for account_name in sorted(all_accounts):
            # 获取实际值
            if not actual_pivot.empty and account_name in actual_pivot.index:
                actual_value = actual_pivot.loc[account_name, period] if period in actual_pivot.columns else 0
            else:
                actual_value = 0

            # 获取预算值
            if not budget_pivot.empty and account_name in budget_pivot.index:
                budget_value = budget_pivot.loc[account_name, period] if period in budget_pivot.columns else 0
            else:
                budget_value = 0

            # 计算差异
            difference = actual_value - budget_value

            result_rows.append({
                "科目名称": account_name,
                "期间": period,
                "实际": actual_value,
                "预算": budget_value,
                "预实差异": difference
            })

    df = pd.DataFrame(result_rows)
    if not df.empty:
        return df.pivot_table(
            index="科目名称",
            columns="期间",
            values=["实际", "预算", "预实差异"],
            aggfunc="first"
        ).reindex(level=1, axis=1, columns=periods).swaplevel(axis=1)

    return pd.DataFrame()


def _createIncomeStatementSummary(
    actual_tb: pd.DataFrame,
    budget_tb: pd.DataFrame,
    periods: list
) -> pd.DataFrame:
    """创建利润表汇总"""
    summary_rows = []

    for period in periods:
        # 实际数据汇总
        if not actual_tb.empty:
            period_actual = actual_tb[actual_tb["period"] == period]
            revenue_actual = period_actual[period_actual["account_type"] == "收入"]["credit_total"].sum()
            expense_actual = period_actual[period_actual["account_type"] == "费用"]["debit_total"].sum()
            net_income_actual = revenue_actual - expense_actual
        else:
            revenue_actual = 0
            expense_actual = 0
            net_income_actual = 0

        # 预算数据汇总
        if not budget_tb.empty:
            period_budget = budget_tb[budget_tb["period"] == period]
            revenue_budget = period_budget[period_budget["account_type"] == "收入"]["credit_total"].sum()
            expense_budget = period_budget[period_budget["account_type"] == "费用"]["debit_total"].sum()
            net_income_budget = revenue_budget - expense_budget
        else:
            revenue_budget = 0
            expense_budget = 0
            net_income_budget = 0

        summary_rows.append({
            "科目名称": "收入合计",
            "期间": period,
            "实际": revenue_actual,
            "预算": revenue_budget,
            "预实差异": revenue_actual - revenue_budget
        })
        summary_rows.append({
            "科目名称": "费用合计",
            "期间": period,
            "实际": expense_actual,
            "预算": expense_budget,
            "预实差异": expense_actual - expense_budget
        })
        summary_rows.append({
            "科目名称": "净利润",
            "期间": period,
            "实际": net_income_actual,
            "预算": net_income_budget,
            "预实差异": net_income_actual - net_income_budget
        })

    df = pd.DataFrame(summary_rows)
    if not df.empty:
        df_pivot = df.pivot_table(
            index="科目名称",
            columns="期间",
            values=["实际", "预算", "预实差异"],
            aggfunc="first"
        )
        return df_pivot.reindex(["收入合计", "费用合计", "净利润"])

    return pd.DataFrame()


def _renderBudgetComparisonCharts(
    actual_tb: pd.DataFrame,
    budget_tb: pd.DataFrame,
    accounts: pd.DataFrame,
    periods: list
) -> None:
    """渲染预实对比图表"""
    st.subheader("预实对比可视化")

    chart_type = st.selectbox(
        "选择图表类型",
        ["资产负债表对比", "利润表对比", "预实差异分析"]
    )

    if chart_type == "资产负债表对比":
        _renderBalanceSheetComparisonChart(actual_tb, budget_tb, accounts, periods)
    elif chart_type == "利润表对比":
        _renderIncomeStatementComparisonChart(actual_tb, budget_tb, accounts, periods)
    elif chart_type == "预实差异分析":
        _renderDifferenceAnalysisChart(actual_tb, budget_tb, accounts, periods)


def _renderBalanceSheetComparisonChart(
    actual_tb: pd.DataFrame,
    budget_tb: pd.DataFrame,
    accounts: pd.DataFrame,
    periods: list
) -> None:
    """资产负债表对比图"""
    st.markdown("### 资产负债表对比")

    # 合并科目类型信息
    if not actual_tb.empty:
        actual_tb = actual_tb.merge(
            accounts[["account_code", "account_type", "account_name"]],
            on="account_code",
            how="left"
        )
    if not budget_tb.empty:
        budget_tb = budget_tb.merge(
            accounts[["account_code", "account_type", "account_name"]],
            on="account_code",
            how="left"
        )

    # 选择期间
    selected_period = st.selectbox("选择期间", periods)
    account_type_filter = st.selectbox("选择科目类型", ["资产", "负债", "所有者权益"])

    # 获取数据
    if not actual_tb.empty and "period" in actual_tb.columns and "account_type" in actual_tb.columns:
        actual_data = actual_tb[
            (actual_tb["period"] == selected_period) &
            (actual_tb["account_type"] == account_type_filter)
        ].copy()
    else:
        actual_data = pd.DataFrame()

    if not budget_tb.empty and "period" in budget_tb.columns and "account_type" in budget_tb.columns:
        budget_data = budget_tb[
            (budget_tb["period"] == selected_period) &
            (budget_tb["account_type"] == account_type_filter)
        ].copy()
    else:
        budget_data = pd.DataFrame()

    if actual_data.empty and budget_data.empty:
        st.info(f"该期间无{account_type_filter}数据。")
        return

    # 创建对比图
    fig = go.Figure()

    # 添加实际数据柱状图
    if not actual_data.empty:
        for _, row in actual_data.iterrows():
            fig.add_trace(go.Bar(
                x=[row["account_name"]],
                y=[row["end_balance"]],
                name="实际",
                marker_color="#1f77b4",
                offsetgroup=0
            ))

    # 添加预算数据柱状图
    if not budget_data.empty:
        for _, row in budget_data.iterrows():
            fig.add_trace(go.Bar(
                x=[row["account_name"]],
                y=[row["end_balance"]],
                name="预算",
                marker_color="#ff7f0e",
                offsetgroup=1
            ))

    fig.update_layout(
        barmode="group",
        title=f"{account_type_filter} - 实际 vs 预算 ({selected_period})",
        xaxis_title="科目名称",
        yaxis_title="期末余额",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)


def _renderIncomeStatementComparisonChart(
    actual_tb: pd.DataFrame,
    budget_tb: pd.DataFrame,
    accounts: pd.DataFrame,
    periods: list
) -> None:
    """利润表对比图"""
    st.markdown("### 利润表对比")

    # 合并科目类型信息
    if not actual_tb.empty:
        actual_tb = actual_tb.merge(
            accounts[["account_code", "account_type", "account_name"]],
            on="account_code",
            how="left"
        )
    if not budget_tb.empty:
        budget_tb = budget_tb.merge(
            accounts[["account_code", "account_type", "account_name"]],
            on="account_code",
            how="left"
        )

    # 选择期间
    selected_period = st.selectbox("选择期间", periods)
    account_type_filter = st.selectbox("选择科目类型", ["收入", "费用"])

    # 确定使用的列
    value_column = "credit_total" if account_type_filter == "收入" else "debit_total"
    y_title = "贷方发生额" if account_type_filter == "收入" else "借方发生额"

    # 获取数据
    if not actual_tb.empty and "period" in actual_tb.columns and "account_type" in actual_tb.columns:
        actual_data = actual_tb[
            (actual_tb["period"] == selected_period) &
            (actual_tb["account_type"] == account_type_filter)
        ].copy()
    else:
        actual_data = pd.DataFrame()

    if not budget_tb.empty and "period" in budget_tb.columns and "account_type" in budget_tb.columns:
        budget_data = budget_tb[
            (budget_tb["period"] == selected_period) &
            (budget_tb["account_type"] == account_type_filter)
        ].copy()
    else:
        budget_data = pd.DataFrame()

    if actual_data.empty and budget_data.empty:
        st.info(f"该期间无{account_type_filter}数据。")
        return

    # 创建对比图
    fig = go.Figure()

    # 添加实际数据柱状图
    if not actual_data.empty:
        for _, row in actual_data.iterrows():
            fig.add_trace(go.Bar(
                x=[row["account_name"]],
                y=[row[value_column]],
                name="实际",
                marker_color="#1f77b4",
                offsetgroup=0
            ))

    # 添加预算数据柱状图
    if not budget_data.empty:
        for _, row in budget_data.iterrows():
            fig.add_trace(go.Bar(
                x=[row["account_name"]],
                y=[row[value_column]],
                name="预算",
                marker_color="#ff7f0e",
                offsetgroup=1
            ))

    fig.update_layout(
        barmode="group",
        title=f"{account_type_filter} - 实际 vs 预算 ({selected_period})",
        xaxis_title="科目名称",
        yaxis_title=y_title,
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)


def _renderDifferenceAnalysisChart(
    actual_tb: pd.DataFrame,
    budget_tb: pd.DataFrame,
    accounts: pd.DataFrame,
    periods: list
) -> None:
    """预实差异分析图"""
    st.markdown("### 预实差异分析")

    # 合并科目类型信息
    if not actual_tb.empty:
        actual_tb = actual_tb.merge(
            accounts[["account_code", "account_type", "account_name"]],
            on="account_code",
            how="left"
        )
    if not budget_tb.empty:
        budget_tb = budget_tb.merge(
            accounts[["account_code", "account_type", "account_name"]],
            on="account_code",
            how="left"
        )

    # 选择期间
    selected_period = st.selectbox("选择期间", periods, key="diff_period")
    account_type_filter = st.selectbox("选择科目类型", ["全部", "资产", "负债", "所有者权益", "收入", "费用"], key="diff_type")

    # 过滤数据
    if account_type_filter == "全部":
        if not actual_tb.empty and "period" in actual_tb.columns:
            actual_data = actual_tb[actual_tb["period"] == selected_period].copy()
        else:
            actual_data = pd.DataFrame()
        
        if not budget_tb.empty and "period" in budget_tb.columns:
            budget_data = budget_tb[budget_tb["period"] == selected_period].copy()
        else:
            budget_data = pd.DataFrame()
    else:
        if not actual_tb.empty and "period" in actual_tb.columns and "account_type" in actual_tb.columns:
            actual_data = actual_tb[
                (actual_tb["period"] == selected_period) &
                (actual_tb["account_type"] == account_type_filter)
            ].copy()
        else:
            actual_data = pd.DataFrame()
        
        if not budget_tb.empty and "period" in budget_tb.columns and "account_type" in budget_tb.columns:
            budget_data = budget_tb[
                (budget_tb["period"] == selected_period) &
                (budget_tb["account_type"] == account_type_filter)
            ].copy()
        else:
            budget_data = pd.DataFrame()

    if actual_data.empty and budget_data.empty:
        st.info(f"该期间无{account_type_filter}数据。")
        return

    # 计算差异
    difference_data = []

    # 确定使用的值列
    value_column = "end_balance"
    if account_type_filter == "收入":
        value_column = "credit_total"
    elif account_type_filter == "费用":
        value_column = "debit_total"

    # 获取所有科目
    all_accounts = set()
    if not actual_data.empty:
        all_accounts.update(actual_data["account_name"])
    if not budget_data.empty:
        all_accounts.update(budget_data["account_name"])

    for account_name in sorted(all_accounts):
        actual_value = actual_data[actual_data["account_name"] == account_name][value_column].sum() if not actual_data.empty else 0
        budget_value = budget_data[budget_data["account_name"] == account_name][value_column].sum() if not budget_data.empty else 0
        difference = actual_value - budget_value

        difference_data.append({
            "科目名称": account_name,
            "实际": actual_value,
            "预算": budget_value,
            "预实差异": difference
        })

    diff_df = pd.DataFrame(difference_data)

    if diff_df.empty:
        st.info("无数据可显示。")
        return

    # 显示差异表
    st.dataframe(
        diff_df.style.format({"实际": "{:.2f}", "预算": "{:.2f}", "预实差异": "{:.2f}"}),
        use_container_width=True,
        hide_index=True
    )

    # 差异分析图
    fig = go.Figure()

    # 正差异用绿色，负差异用红色
    colors = ['#2ca02c' if d >= 0 else '#d62728' for d in diff_df["预实差异"]]

    fig.add_trace(go.Bar(
        x=diff_df["科目名称"],
        y=diff_df["预实差异"],
        marker_color=colors,
        text=diff_df["预实差异"].apply(lambda x: f"{x:.2f}"),
        textposition="outside"
    ))

    fig.update_layout(
        title=f"预实差异分析 ({selected_period} - {account_type_filter})",
        xaxis_title="科目名称",
        yaxis_title="预实差异",
        height=500,
        showlegend=False
    )

    # 添加零线
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    st.plotly_chart(fig, use_container_width=True)


def _renderBudgetAccountDetail(
    actual_tb: pd.DataFrame,
    budget_tb: pd.DataFrame,
    accounts: pd.DataFrame,
    periods: list
) -> None:
    """渲染科目明细（实际数和预算数）"""
    st.subheader("科目明细")

    # 合并科目类型信息
    if not actual_tb.empty:
        actual_tb = actual_tb.merge(
            accounts[["account_code", "account_type", "account_name"]],
            on="account_code",
            how="left"
        )
    if not budget_tb.empty:
        budget_tb = budget_tb.merge(
            accounts[["account_code", "account_type", "account_name"]],
            on="account_code",
            how="left"
        )

    # 选择显示类型
    detail_type = st.radio(
        "选择明细类型",
        ["实际数科目明细", "预算数科目明细"],
        horizontal=True
    )

    if detail_type == "实际数科目明细":
        if actual_tb.empty:
            st.info("暂无实际数据。")
            return

        # 过滤期间
        filtered_data = actual_tb[actual_tb["period"].isin(periods)].copy()
    else:
        if budget_tb.empty:
            st.info("暂无预算数据。")
            return

        # 过滤期间
        filtered_data = budget_tb[budget_tb["period"].isin(periods)].copy()

    if filtered_data.empty:
        st.info("所选期间无数据。")
        return

    # 格式化显示
    display_columns = ["account_code", "account_name", "period",
                   "begin_balance", "debit_total", "credit_total", "end_balance"]
    display_data = filtered_data[display_columns].copy()

    # 列名中文
    display_data.columns = ["科目编码", "科目名称", "会计期间",
                        "期初余额", "借方发生额", "贷方发生额", "期末余额"]

    # 数值格式化
    for col in ["期初余额", "借方发生额", "贷方发生额", "期末余额"]:
        display_data[col] = display_data[col].apply(lambda x: f"{x:,.2f}")

    st.dataframe(display_data, use_container_width=True, hide_index=True)

    # 统计信息
    st.markdown("---")
    st.markdown("### 📈 统计摘要")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_accounts = filtered_data["account_code"].nunique()
        st.metric("科目数量", f"{total_accounts} 个")

    with col2:
        total_debit = filtered_data["debit_total"].sum()
        st.metric("借方总额", f"{total_debit:,.2f}")

    with col3:
        total_credit = filtered_data["credit_total"].sum()
        st.metric("贷方总额", f"{total_credit:,.2f}")


def _renderSampleView() -> None:
    """展示示例视图"""
    st.markdown("### 📋 预实分析预览（示例）")
    st.markdown("上传数据后，您将看到如下格式的预实分析报表：")

    sample_data = {
        "科目名称": ["银行存款", "生活费用"],
        "期间": "2024-01",
        "实际": [10000.00, 3000.00],
        "预算": [12000.00, 2500.00],
        "预实差异": [-2000.00, 500.00],
    }
    st.dataframe(pd.DataFrame(sample_data), use_container_width=True, hide_index=True)