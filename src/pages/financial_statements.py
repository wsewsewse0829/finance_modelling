"""
会计报表页面
展示资产负债表、利润表等财务报表，支持可视化
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils.data_manager import loadTrialBalance, loadReport, loadAccounts
from src.utils.accounting import generateReport, validateReport


def renderFinancialStatementsPage() -> None:
    """渲染会计报表页面"""
    st.title("📊 会计报表")
    st.markdown("---")

    # 加载数据
    trial_balance = loadTrialBalance()
    accounts = loadAccounts()

    if trial_balance.empty:
        st.warning("暂无数据。请先在「数据上传」页面上传序时账数据。")
        _renderSampleView()
        return

    # 生成报表
    report = generateReport(trial_balance, accounts)

    if report.empty:
        st.warning("无法生成报表，请检查数据。")
        return

    # 报表平衡校验
    is_balanced, errors = validateReport(report)
    if not is_balanced:
        st.error("⚠️ 会计报表不平衡！")
        for error in errors:
            st.error(error)

    # 期间选择
    periods = sorted(report["period"].unique())
    selected_periods = st.multiselect(
        "选择会计期间",
        periods,
        default=periods[-3:] if len(periods) >= 3 else periods,
    )

    if not selected_periods:
        st.info("请选择至少一个会计期间。")
        return

    filtered_report = report[report["period"].isin(selected_periods)]

    # 报表展示标签页
    tab_bs, tab_pl, tab_chart = st.tabs(["资产负债表", "利润表", "可视化图表"])

    with tab_bs:
        _renderBalanceSheet(filtered_report, selected_periods)

    with tab_pl:
        _renderIncomeStatement(filtered_report, selected_periods)

    with tab_chart:
        _renderCharts(filtered_report, selected_periods)


def _renderBalanceSheet(report: pd.DataFrame, periods: list) -> None:
    """渲染资产负债表"""
    st.subheader("资产负债表")
    bs_data = report[report["report_type"] == "资产负债表"]

    if bs_data.empty:
        st.info("暂无资产负债表数据。")
        return

    # 透视表：行为项目，列为期间
    pivot = bs_data.pivot_table(
        index="item", columns="period", values="amount", aggfunc="sum"
    ).reindex(["资产总计", "负债总计", "所有者权益总计"])

    st.dataframe(pivot.style.format("{:.2f}"), use_container_width=True)


def _renderIncomeStatement(report: pd.DataFrame, periods: list) -> None:
    """渲染利润表"""
    st.subheader("利润表")
    pl_data = report[report["report_type"] == "利润表"]

    if pl_data.empty:
        st.info("暂无利润表数据。")
        return

    pivot = pl_data.pivot_table(
        index="item", columns="period", values="amount", aggfunc="sum"
    ).reindex(["收入合计", "费用合计", "净利润"])

    st.dataframe(pivot.style.format("{:.2f}"), use_container_width=True)


def _renderCharts(report: pd.DataFrame, periods: list) -> None:
    """渲染可视化图表"""
    st.subheader("可视化分析")

    chart_type = st.selectbox("选择图表类型", ["资产负债结构", "收入费用趋势", "净利润趋势"])

    if chart_type == "资产负债结构":
        bs_data = report[report["report_type"] == "资产负债表"]
        if not bs_data.empty:
            fig = px.bar(
                bs_data, x="period", y="amount", color="item",
                barmode="group", title="资产负债结构",
                labels={"period": "会计期间", "amount": "金额", "item": "项目"}
            )
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "收入费用趋势":
        pl_data = report[report["report_type"] == "利润表"]
        pl_data = pl_data[pl_data["item"].isin(["收入合计", "费用合计"])]
        if not pl_data.empty:
            fig = px.line(
                pl_data, x="period", y="amount", color="item",
                title="收入费用趋势",
                labels={"period": "会计期间", "amount": "金额", "item": "项目"},
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "净利润趋势":
        pl_data = report[report["report_type"] == "利润表"]
        net_income = pl_data[pl_data["item"] == "净利润"]
        if not net_income.empty:
            fig = px.bar(
                net_income, x="period", y="amount",
                title="净利润趋势",
                labels={"period": "会计期间", "amount": "金额"},
                color="amount",
                color_continuous_scale=["red", "green"],
            )
            st.plotly_chart(fig, use_container_width=True)


def _renderSampleView() -> None:
    """展示示例报表视图"""
    st.markdown("### 📋 报表预览（示例）")
    st.markdown("上传数据后，您将看到如下格式的财务报表：")

    sample_data = {
        "项目": ["资产总计", "负债总计", "所有者权益总计"],
        "2024-01": [50000.00, 10000.00, 40000.00],
        "2024-02": [52000.00, 9500.00, 42500.00],
        "2024-03": [55000.00, 9000.00, 46000.00],
    }
    st.dataframe(pd.DataFrame(sample_data), use_container_width=True)
