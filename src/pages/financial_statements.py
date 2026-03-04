"""
会计报表页面
展示资产负债表、利润表等财务报表，支持可视化
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils.data_manager import loadGeneralLedger, loadAccounts
from src.utils.accounting import generateTrialBalance, generateReport, validateReport


def renderFinancialStatementsPage() -> None:
    """渲染会计报表页面"""
    st.title("📊 会计报表")
    st.markdown("---")

    # 加载数据
    ledger = loadGeneralLedger()
    accounts = loadAccounts()

    # 过滤只显示实际数据
    actual_ledger = ledger[ledger["actual_budget"] == "实际"].copy()
    
    if actual_ledger.empty:
        st.warning("暂无实际数据。请先在「数据上传」页面上传序时账数据。")
        _renderSampleView()
        return
    
    # 从实际数据生成科目余额表
    from src.utils.accounting import generateTrialBalance
    trial_balance = generateTrialBalance(actual_ledger, accounts)

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
        default=periods,  # 默认选择全部期间
    )

    if not selected_periods:
        st.info("请选择至少一个会计期间。")
        return

    # 过滤科目余额表数据（显示所有科目，不限制长度）
    tb_filtered = trial_balance[
        trial_balance["period"].isin(selected_periods)
    ].copy()

    # 合并科目类型（只选择需要的列避免重复）
    tb_filtered["account_code"] = tb_filtered["account_code"].astype(str)
    accounts_str = accounts.copy()
    accounts_str["account_code"] = accounts_str["account_code"].astype(str)
    # 如果科目余额表已有account_name，先删除再合并
    if "account_name" in tb_filtered.columns:
        tb_filtered = tb_filtered.drop(columns=["account_name"])
    tb_filtered = tb_filtered.merge(
        accounts_str[["account_code", "account_type", "account_name"]],
        on="account_code",
        how="left"
    )

    # 过滤报表数据
    filtered_report = report[report["period"].isin(selected_periods)]

    # 报表展示标签页
    tab_bs, tab_pl, tab_chart, tab_detail = st.tabs([
        "资产负债表", "利润表", "可视化图表", "科目明细"
    ])

    with tab_bs:
        _renderBalanceSheet(tb_filtered, selected_periods)

    with tab_pl:
        _renderIncomeStatement(tb_filtered, selected_periods)

    with tab_chart:
        _renderCharts(tb_filtered, selected_periods)

    with tab_detail:
        _renderAccountDetail(tb_filtered, selected_periods)


def _renderBalanceSheet(trial_balance: pd.DataFrame, periods: list) -> None:
    """渲染资产负债表"""
    st.subheader("资产负债表")
    
    if trial_balance.empty:
        st.info("暂无资产负债表数据。")
        return
    
    # 按科目类型分组
    account_types = ["资产", "负债", "所有者权益"]
    
    for account_type in account_types:
        type_data = trial_balance[trial_balance["account_type"] == account_type]
        
        if type_data.empty:
            continue
        
        # 创建透视表：行=科目名称，列=期间，值=期末余额
        pivot = type_data.pivot_table(
            index="account_name",
            columns="period",
            values="end_balance",
            aggfunc="sum"
        )
        
        # 重新排序列（按期间）
        pivot = pivot.reindex(columns=periods)
        
        # 按科目编码排序
        type_data_sorted = type_data.sort_values("account_code")
        account_names_ordered = type_data_sorted["account_name"].unique()
        pivot = pivot.reindex(account_names_ordered)
        
        # 显示表格
        st.markdown(f"#### {account_type}")
        st.dataframe(pivot.style.format("{:.2f}"), use_container_width=True)
    
    # 显示汇总数据
    st.markdown("---")
    
    # 计算各期间汇总
    summary_data = []
    for period in periods:
        period_data = trial_balance[trial_balance["period"] == period]
        
        asset_total = period_data[period_data["account_type"] == "资产"]["end_balance"].sum()
        liability_total = period_data[period_data["account_type"] == "负债"]["end_balance"].sum()
        
        # 所有者权益包括：
        # 1. 所有者权益类科目的期末余额
        # 2. 收入科目的净额（收入增加所有者权益）
        # 3. 费用科目的净额（费用减少所有者权益）
        equity_accounts_total = period_data[period_data["account_type"] == "所有者权益"]["end_balance"].sum()
        revenue_total = period_data[period_data["account_type"] == "收入"]["end_balance"].sum()
        expense_total = period_data[period_data["account_type"] == "费用"]["end_balance"].sum()
        equity_total = equity_accounts_total + revenue_total - expense_total
        
        summary_data.append({
            "科目名称": "资产总计",
            "期间": period,
            "金额": asset_total
        })
        summary_data.append({
            "科目名称": "负债总计",
            "期间": period,
            "金额": liability_total
        })
        summary_data.append({
            "科目名称": "所有者权益总计",
            "期间": period,
            "金额": equity_total
        })
    
    summary_df = pd.DataFrame(summary_data)
    pivot = summary_df.pivot_table(
        index="科目名称",
        columns="期间",
        values="金额",
        aggfunc="sum"
    ).reindex(["资产总计", "负债总计", "所有者权益总计"])
    
    st.dataframe(pivot.style.format("{:.2f}"), use_container_width=True)


def _renderIncomeStatement(trial_balance: pd.DataFrame, periods: list) -> None:
    """渲染利润表"""
    st.subheader("利润表")
    
    if trial_balance.empty:
        st.info("暂无利润表数据。")
        return
    
    # 按科目类型分组
    account_types = ["收入", "费用"]
    
    for account_type in account_types:
        type_data = trial_balance[trial_balance["account_type"] == account_type]
        
        if type_data.empty:
            continue
        
        # 创建透视表：行=科目名称，列=期间
        # 收入显示贷方发生额，费用显示借方发生额
        if account_type == "收入":
            pivot = type_data.pivot_table(
                index="account_name",
                columns="period",
                values="credit_total",
                aggfunc="sum"
            )
        else:  # 费用
            pivot = type_data.pivot_table(
                index="account_name",
                columns="period",
                values="debit_total",
                aggfunc="sum"
            )
        
        # 重新排序列（按期间）
        pivot = pivot.reindex(columns=periods)
        
        # 按科目编码排序
        type_data_sorted = type_data.sort_values("account_code")
        account_names_ordered = type_data_sorted["account_name"].unique()
        pivot = pivot.reindex(account_names_ordered)
        
        # 添加合计列
        if len(periods) > 1:
            pivot["合计"] = pivot.sum(axis=1)
        
        # 显示表格
        st.dataframe(pivot.style.format("{:.2f}"), use_container_width=True)
    
    # 显示汇总数据
    st.markdown("---")
    
    # 计算各期间汇总
    summary_data = []
    for period in periods:
        period_data = trial_balance[trial_balance["period"] == period]
        
        revenue_total = period_data[period_data["account_type"] == "收入"]["credit_total"].sum()
        expense_total = period_data[period_data["account_type"] == "费用"]["debit_total"].sum()
        net_income = revenue_total - expense_total
        
        summary_data.append({
            "科目名称": "收入合计",
            "期间": period,
            "金额": revenue_total
        })
        summary_data.append({
            "科目名称": "费用合计",
            "期间": period,
            "金额": expense_total
        })
        summary_data.append({
            "科目名称": "净利润",
            "期间": period,
            "金额": net_income
        })
    
    summary_df = pd.DataFrame(summary_data)
    pivot = summary_df.pivot_table(
        index="科目名称",
        columns="期间",
        values="金额",
        aggfunc="sum"
    ).reindex(["收入合计", "费用合计", "净利润"])
    
    # 添加合计列
    if len(periods) > 1:
        pivot["合计"] = pivot.sum(axis=1)
    
    st.dataframe(pivot.style.format("{:.2f}"), use_container_width=True)


def _renderCharts(trial_balance: pd.DataFrame, periods: list) -> None:
    """渲染可视化图表"""
    st.subheader("可视化分析")

    if trial_balance.empty:
        st.info("暂无科目数据。")
        return

    chart_type = st.selectbox(
        "选择图表类型",
        ["资产结构分析", "负债结构分析", "所有者权益结构分析", 
         "收入结构分析", "费用结构分析", "科目趋势分析"]
    )

    if chart_type == "资产结构分析":
        _renderAssetStructure(trial_balance, periods)
    elif chart_type == "负债结构分析":
        _renderLiabilityStructure(trial_balance, periods)
    elif chart_type == "所有者权益结构分析":
        _renderEquityStructure(trial_balance, periods)
    elif chart_type == "收入结构分析":
        _renderRevenueStructure(trial_balance, periods)
    elif chart_type == "费用结构分析":
        _renderExpenseStructure(trial_balance, periods)
    elif chart_type == "科目趋势分析":
        _renderAccountTrend(trial_balance, periods)


def _renderAssetStructure(trial_balance: pd.DataFrame, periods: list) -> None:
    """资产结构分析"""
    st.markdown("### 资产结构分析")
    
    asset_data = trial_balance[trial_balance["account_type"] == "资产"]
    
    if asset_data.empty:
        st.info("暂无资产数据。")
        return
    
    # 按期间筛选
    selected_period = st.selectbox("选择期间", periods)
    period_data = asset_data[asset_data["period"] == selected_period]
    
    if period_data.empty:
        st.info("该期间无资产数据。")
        return
    
    # 按科目编码分组显示
    period_data = period_data.sort_values("account_code")
    
    # 饼图
    fig = px.pie(
        period_data,
        values="end_balance",
        names="account_name",
        title=f"资产结构分析 ({selected_period})",
        hover_data=["account_code", "end_balance"],
        labels={"account_name": "科目名称", "end_balance": "期末余额"}
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)
    
    # 柱状图
    fig_bar = px.bar(
        period_data,
        x="account_name",
        y="end_balance",
        title=f"资产明细 ({selected_period})",
        color="account_code",
        labels={"account_name": "科目名称", "end_balance": "期末余额"},
        text="end_balance"
    )
    fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_bar.update_layout(showlegend=False)  # 隐藏图例，X轴已显示科目名称
    st.plotly_chart(fig_bar, use_container_width=True)


def _renderLiabilityStructure(trial_balance: pd.DataFrame, periods: list) -> None:
    """负债结构分析"""
    st.markdown("### 负债结构分析")
    
    liability_data = trial_balance[trial_balance["account_type"] == "负债"]
    
    if liability_data.empty:
        st.info("暂无负债数据。")
        return
    
    selected_period = st.selectbox("选择期间", periods)
    period_data = liability_data[liability_data["period"] == selected_period]
    
    if period_data.empty:
        st.info("该期间无负债数据。")
        return
    
    period_data = period_data.sort_values("account_code")
    
    # 饼图
    fig = px.pie(
        period_data,
        values="end_balance",
        names="account_name",
        title=f"负债结构分析 ({selected_period})",
        hover_data=["account_code", "end_balance"],
        labels={"account_name": "科目名称", "end_balance": "期末余额"}
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)


def _renderEquityStructure(trial_balance: pd.DataFrame, periods: list) -> None:
    """所有者权益结构分析"""
    st.markdown("### 所有者权益结构分析")
    
    equity_data = trial_balance[trial_balance["account_type"] == "所有者权益"]
    
    if equity_data.empty:
        st.info("暂无所有者权益数据。")
        return
    
    selected_period = st.selectbox("选择期间", periods)
    period_data = equity_data[equity_data["period"] == selected_period]
    
    if period_data.empty:
        st.info("该期间无所有者权益数据。")
        return
    
    period_data = period_data.sort_values("account_code")
    
    fig = px.bar(
        period_data,
        x="account_name",
        y="end_balance",
        title=f"所有者权益明细 ({selected_period})",
        color="account_code",
        labels={"account_name": "科目名称", "end_balance": "期末余额"},
        text="end_balance"
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(showlegend=False)  # 隐藏图例，X轴已显示科目名称
    st.plotly_chart(fig, use_container_width=True)


def _renderRevenueStructure(trial_balance: pd.DataFrame, periods: list) -> None:
    """收入结构分析"""
    st.markdown("### 收入结构分析")
    
    revenue_data = trial_balance[trial_balance["account_type"] == "收入"]
    
    if revenue_data.empty:
        st.info("暂无收入数据。")
        return
    
    selected_periods = st.multiselect("选择期间", periods, default=periods[:1])
    
    if not selected_periods:
        st.info("请至少选择一个期间。")
        return
    
    period_data = revenue_data[revenue_data["period"].isin(selected_periods)]
    
    if period_data.empty:
        st.info("所选期间无收入数据。")
        return
    
    period_data = period_data.sort_values(["period", "account_code"])
    
    # 饼图 - 按贷方发生额
    fig = px.pie(
        period_data,
        values="credit_total",
        names="account_name",
        title=f"收入结构分析 ({', '.join(selected_periods)})",
        hover_data=["account_code", "credit_total"],
        labels={"account_name": "科目名称", "credit_total": "贷方发生额"}
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)
    
    # 柱状图 - 多个期间时不显示数据标签，避免重叠
    fig_bar = px.bar(
        period_data,
        x="account_name",
        y="credit_total",
        title=f"收入明细 ({', '.join(selected_periods)})",
        color="period",  # 按期间分组显示
        labels={"account_name": "科目名称", "credit_total": "贷方发生额", "period": "期间"},
        barmode="group"  # 分组显示
    )
    
    # 单个期间时显示数据标签，多个期间时不显示避免重叠
    if len(selected_periods) == 1:
        fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    
    fig_bar.update_layout(showlegend=True)  # 显示图例，区分不同期间
    st.plotly_chart(fig_bar, use_container_width=True)


def _renderExpenseStructure(trial_balance: pd.DataFrame, periods: list) -> None:
    """费用结构分析"""
    st.markdown("### 费用结构分析")
    
    expense_data = trial_balance[trial_balance["account_type"] == "费用"]
    
    if expense_data.empty:
        st.info("暂无费用数据。")
        return
    
    selected_periods = st.multiselect("选择期间", periods, default=periods[:1])
    
    if not selected_periods:
        st.info("请至少选择一个期间。")
        return
    
    period_data = expense_data[expense_data["period"].isin(selected_periods)]
    
    if period_data.empty:
        st.info("所选期间无费用数据。")
        return
    
    period_data = period_data.sort_values(["period", "account_code"])
    
    # 饼图 - 按借方发生额
    fig = px.pie(
        period_data,
        values="debit_total",
        names="account_name",
        title=f"费用结构分析 ({', '.join(selected_periods)})",
        hover_data=["account_code", "debit_total"],
        labels={"account_name": "科目名称", "debit_total": "借方发生额"}
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)
    
    # 柱状图 - 多个期间时不显示数据标签，避免重叠
    fig_bar = px.bar(
        period_data,
        x="account_name",
        y="debit_total",
        title=f"费用明细 ({', '.join(selected_periods)})",
        color="period",  # 按期间分组显示
        labels={"account_name": "科目名称", "debit_total": "借方发生额", "period": "期间"},
        barmode="group"  # 分组显示
    )
    
    # 单个期间时显示数据标签，多个期间时不显示避免重叠
    if len(selected_periods) == 1:
        fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    
    fig_bar.update_layout(showlegend=True)  # 显示图例，区分不同期间
    st.plotly_chart(fig_bar, use_container_width=True)


def _renderAccountTrend(trial_balance: pd.DataFrame, periods: list) -> None:
    """科目趋势分析"""
    st.markdown("### 科目趋势分析")
    
    # 选择科目类型
    account_type = st.selectbox(
        "选择科目类型",
        ["全部", "资产", "负债", "所有者权益", "收入", "费用"]
    )
    
    if account_type == "全部":
        filtered_data = trial_balance
    else:
        filtered_data = trial_balance[trial_balance["account_type"] == account_type]
    
    if filtered_data.empty:
        st.info(f"暂无{account_type}数据。")
        return
    
    # 选择要显示的科目
    account_list = filtered_data.groupby(["account_code", "account_name"]).first().reset_index()
    selected_accounts = st.multiselect(
        "选择科目",
        options=account_list.apply(lambda x: f"{x['account_code']} - {x['account_name']}", axis=1),
        default=account_list.apply(lambda x: f"{x['account_code']} - {x['account_name']}", axis=1)[:5]
    )
    
    if not selected_accounts:
        st.info("请选择至少一个科目。")
        return
    
    # 提取科目编码
    selected_codes = [s.split(" - ")[0] for s in selected_accounts]
    
    # 过滤数据
    trend_data = filtered_data[filtered_data["account_code"].isin(selected_codes)].sort_values(["account_code", "period"])
    
    # 根据科目类型确定显示的数值和标题
    if account_type in ["收入", "费用"]:
        if account_type == "收入":
            # 收入类科目使用贷方发生额
            y_column = "credit_total"
            y_label = "贷方发生额"
        else:
            # 费用类科目使用借方发生额
            y_column = "debit_total"
            y_label = "借方发生额"
        chart_title = f"科目{y_label}趋势"
    else:
        # 资产、负债、所有者权益使用期末余额
        y_column = "end_balance"
        y_label = "期末余额"
        chart_title = "科目期末余额趋势"
    
    # 趋势图
    fig = px.line(
        trend_data,
        x="period",
        y=y_column,
        color="account_name",
        title=chart_title,
        labels={"period": "会计期间", y_column: y_label, "account_name": "科目名称"},
        markers=True,
    )
    st.plotly_chart(fig, use_container_width=True)


def _renderAccountDetail(trial_balance: pd.DataFrame, periods: list) -> None:
    """渲染科目明细"""
    st.subheader("科目明细")
    
    if trial_balance.empty:
        st.info("暂无科目数据。")
        return
    
    # 按科目类型筛选
    account_type_filter = st.selectbox(
        "筛选科目类型",
        ["全部", "资产", "负债", "所有者权益", "收入", "费用"],
        key="account_type_filter"
    )
    
    if account_type_filter == "全部":
        filtered_data = trial_balance
    else:
        filtered_data = trial_balance[trial_balance["account_type"] == account_type_filter]
    
    if filtered_data.empty:
        st.info(f"暂无{account_type_filter}类科目数据。")
        return
    
    # 按科目编码和科目名称排序
    filtered_data = filtered_data.sort_values(["account_type", "account_code"])
    
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