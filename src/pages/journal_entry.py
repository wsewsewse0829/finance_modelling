"""
手动录入分录页面
支持多科目、分录模板、自动结转等功能
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.utils.data_manager import (
    loadAccounts,
    saveGeneralLedger,
    loadGeneralLedger,
    saveJournalTemplate,
    loadJournalTemplates,
    getJournalTemplate,
    deleteJournalTemplate
)
from src.utils.accounting import (
    validateJournalEntries,
    generateClosingStep1,
    generateClosingStep2
)


def renderJournalEntryPage() -> None:
    """渲染手动录入分录页面"""
    st.title("📝 手动录入分录")
    st.markdown("---")

    # 初始化 session state
    _init_session_state()

    # 加载科目表
    accounts = loadAccounts()
    if accounts.empty:
        st.warning("暂无科目数据。请先在「科目管理」页面添加科目。")
        return

    # 基础信息
    _render_basic_info()

    # 分录明细
    _render_entry_details(accounts)

    # 自动结转选项
    closing_enabled = _render_closing_option(accounts)

    # 平衡校验和预览
    all_entries = _render_balance_check(accounts, closing_enabled)

    # 操作按钮
    _render_action_buttons(all_entries, closing_enabled)

    # 模板管理
    _render_template_management()


def _init_session_state() -> None:
    """初始化 session state"""
    if "debit_entries" not in st.session_state:
        st.session_state.debit_entries = [{}]
    if "credit_entries" not in st.session_state:
        st.session_state.credit_entries = [{}]
    if "closing_enabled" not in st.session_state:
        st.session_state.closing_enabled = False
    if "actual_budget" not in st.session_state:
        st.session_state.actual_budget = "实际"
    if "period" not in st.session_state:
        st.session_state.period = ""
    if "entry_date" not in st.session_state:
        st.session_state.entry_date = ""
    if "summary" not in st.session_state:
        st.session_state.summary = ""
    if "template_selected" not in st.session_state:
        st.session_state.template_selected = None


def _render_basic_info() -> None:
    """渲染基础信息"""
    st.markdown("### 基础信息")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.session_state.actual_budget = st.radio(
            "数据类型",
            ["实际", "预算"],
            horizontal=True,
            key="actual_budget_radio"
        )
    
    with col2:
        # 默认当前月份
        current_month = datetime.now().strftime("%Y-%m")
        st.session_state.period = st.text_input(
            "会计期间",
            value=st.session_state.period or current_month,
            placeholder="YYYY-MM（如 2024-03）",
            key="period_input"
        )
    
    with col3:
        today = datetime.now().strftime("%Y-%m-%d")
        st.session_state.entry_date = st.text_input(
            "凭证日期",
            value=st.session_state.entry_date or today,
            placeholder="YYYY-MM-DD（如 2024-03-15）",
            key="date_input"
        )
    
    with col4:
        st.session_state.summary = st.text_input(
            "摘要",
            value=st.session_state.summary,
            placeholder="如：工资收入",
            key="summary_input"
        )


def _render_entry_details(accounts: pd.DataFrame) -> None:
    """渲染分录明细"""
    st.markdown("### 分录明细")
    
    # 准备科目选项
    account_options = accounts.apply(
        lambda x: f"{x['account_code']} - {x['account_name']}",
        axis=1
    ).tolist()
    
    # 创建选项到索引的映射（更稳健的方法）
    option_to_index = {option: idx for idx, option in enumerate(account_options)}
    
    # 借方科目
    st.markdown("#### 借方科目")
    col_debit1, col_debit2, col_debit3 = st.columns([4, 3, 1])
    
    for i, entry in enumerate(st.session_state.debit_entries):
        with st.container():
            cols = st.columns([4, 3, 1])
            with cols[0]:
                selected = st.selectbox(
                    f"借方科目 {i+1}",
                    account_options,
                    index=0 if not entry else entry.get("account_option_index", 0),
                    key=f"debit_account_{i}"
                )
                # 保存选择的科目信息
                if selected:
                    selected_index = option_to_index[selected]
                    account_info = accounts.iloc[selected_index]
                    entry["account_code"] = account_info["account_code"]
                    entry["account_name"] = account_info["account_name"]
                    entry["account_option_index"] = selected_index
            
            with cols[1]:
                entry["amount"] = st.number_input(
                    "借方金额",
                    value=entry.get("amount", 0.0),
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    key=f"debit_amount_{i}"
                )
            
            with cols[2]:
                if st.button("✕", key=f"delete_debit_{i}"):
                    st.session_state.debit_entries.pop(i)
                    st.rerun()
    
    # 添加借方科目按钮
    if st.button("➕ 添加借方科目", key="add_debit"):
        st.session_state.debit_entries.append({})
        st.rerun()
    
    st.markdown("---")
    
    # 贷方科目
    st.markdown("#### 贷方科目")
    col_credit1, col_credit2, col_credit3 = st.columns([4, 3, 1])
    
    for i, entry in enumerate(st.session_state.credit_entries):
        with st.container():
            cols = st.columns([4, 3, 1])
            with cols[0]:
                selected = st.selectbox(
                    f"贷方科目 {i+1}",
                    account_options,
                    index=0 if not entry else entry.get("account_option_index", 0),
                    key=f"credit_account_{i}"
                )
                # 保存选择的科目信息
                if selected:
                    selected_index = option_to_index[selected]
                    account_info = accounts.iloc[selected_index]
                    entry["account_code"] = account_info["account_code"]
                    entry["account_name"] = account_info["account_name"]
                    entry["account_option_index"] = selected_index
            
            with cols[1]:
                entry["amount"] = st.number_input(
                    "贷方金额",
                    value=entry.get("amount", 0.0),
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    key=f"credit_amount_{i}"
                )
            
            with cols[2]:
                if st.button("✕", key=f"delete_credit_{i}"):
                    st.session_state.credit_entries.pop(i)
                    st.rerun()
    
    # 添加贷方科目按钮
    if st.button("➕ 添加贷方科目", key="add_credit"):
        st.session_state.credit_entries.append({})
        st.rerun()


def _render_closing_option(accounts: pd.DataFrame) -> bool:
    """渲染自动结转选项
    
    Returns:
        bool: 是否启用自动结转
    """
    st.markdown("---")
    st.markdown("### 自动结转选项")
    
    # 检测是否有收入或费用科目
    has_revenue_or_expense = False
    all_entries = st.session_state.debit_entries + st.session_state.credit_entries
    
    for entry in all_entries:
        if "account_code" in entry:
            account_info = accounts[accounts["account_code"] == entry["account_code"]]
            if not account_info.empty:
                account_type = account_info.iloc[0]["account_type"]
                if account_type in ["收入", "费用"]:
                    has_revenue_or_expense = True
                    break
    
    if not has_revenue_or_expense:
        st.info("当前分录不包含收入或费用科目，无需结转。")
        return False
    
    st.session_state.closing_enabled = st.checkbox(
        "自动生成结转本期利润分录（两步结转）",
        value=st.session_state.closing_enabled,
        help="""
        第一步：收入/费用 → 本年利润
        第二步：本年利润 → 留存收益
        """
    )
    
    if st.session_state.closing_enabled:
        st.markdown("""
        **结转说明：**
        - 第一步：将收入类科目的贷方金额和费用类科目的借方金额结转至"本年利润"
        - 第二步：将"本年利润"的净额结转至"留存收益"
        - 净利润：本年利润有贷方余额
        - 净亏损：本年利润有借方余额
        """)
    
    return st.session_state.closing_enabled


def _render_balance_check(accounts: pd.DataFrame, closing_enabled: bool) -> pd.DataFrame:
    """渲染平衡校验和分录预览
    
    Args:
        accounts: 科目表
        closing_enabled: 是否启用自动结转
        
    Returns:
        pd.DataFrame: 所有分录数据
    """
    st.markdown("---")
    st.markdown("### 平衡校验")
    
    # 计算借方合计和贷方合计
    debit_total = sum(
        entry.get("amount", 0) 
        for entry in st.session_state.debit_entries 
        if "amount" in entry
    )
    credit_total = sum(
        entry.get("amount", 0) 
        for entry in st.session_state.credit_entries 
        if "amount" in entry
    )
    
    # 显示合计
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "借方合计",
            f"{debit_total:,.2f}",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "贷方合计",
            f"{credit_total:,.2f}",
            delta_color="normal"
        )
    
    with col3:
        is_balanced = abs(debit_total - credit_total) < 0.01
        if is_balanced:
            st.metric(
                "借贷平衡",
                "✅ 是",
                delta_color="normal"
            )
        else:
            diff = abs(debit_total - credit_total)
            st.metric(
                "借贷平衡",
                f"❌ 否（差异：{diff:.2f}）",
                delta_color="normal"
            )
    
    # 生成基础分录数据
    base_entries = _generate_base_entries(
        st.session_state.debit_entries,
        st.session_state.credit_entries
    )
    
    all_entries = base_entries
    
    # 如果启用自动结转，生成结转分录
    if closing_enabled and not base_entries.empty:
        step1_entries = generateClosingStep1(
            base_entries,
            accounts,
            st.session_state.actual_budget,
            st.session_state.period,
            st.session_state.entry_date,
            "结转本期利润"
        )
        
        if not step1_entries.empty:
            step2_entries = generateClosingStep2(
                step1_entries,
                st.session_state.actual_budget,
                st.session_state.period,
                st.session_state.entry_date,
                "结转至留存收益"
            )
            
            if not step2_entries.empty:
                all_entries = pd.concat([all_entries, step1_entries, step2_entries], ignore_index=True)
            else:
                all_entries = pd.concat([all_entries, step1_entries], ignore_index=True)
        else:
            all_entries = all_entries
    
    # 显示分录预览
    _render_entry_preview(all_entries)
    
    return all_entries


def _generate_base_entries(
    debit_entries: list,
    credit_entries: list
) -> pd.DataFrame:
    """生成基础分录数据
    
    Args:
        debit_entries: 借方科目列表
        credit_entries: 贷方科目列表
        
    Returns:
        pd.DataFrame: 基础分录数据
    """
    entries = []
    voucher_no = f"{st.session_state.period}-001"
    
    # 借方分录
    for entry in debit_entries:
        if "account_code" in entry and "amount" in entry and entry["amount"] > 0:
            entries.append({
                "entry_date": st.session_state.entry_date,
                "voucher_no": voucher_no,
                "account_code": entry["account_code"],
                "account_name": entry["account_name"],
                "debit_amount": entry["amount"],
                "credit_amount": 0,
                "summary": st.session_state.summary,
                "actual_budget": st.session_state.actual_budget
            })
    
    # 贷方分录
    for entry in credit_entries:
        if "account_code" in entry and "amount" in entry and entry["amount"] > 0:
            entries.append({
                "entry_date": st.session_state.entry_date,
                "voucher_no": voucher_no,
                "account_code": entry["account_code"],
                "account_name": entry["account_name"],
                "debit_amount": 0,
                "credit_amount": entry["amount"],
                "summary": st.session_state.summary,
                "actual_budget": st.session_state.actual_budget
            })
    
    if not entries:
        return pd.DataFrame()
    
    return pd.DataFrame(entries)[
        "entry_date", "voucher_no", "account_code", "account_name",
        "debit_amount", "credit_amount", "summary", "actual_budget"
    ]


def _render_entry_preview(entries: pd.DataFrame) -> None:
    """渲染分录预览"""
    if entries.empty:
        return
    
    st.markdown("---")
    st.markdown("### 分录预览")
    
    # 按凭证号分组
    grouped = entries.groupby("voucher_no")
    
    for voucher_no, group in grouped:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"📄 凭证：{voucher_no}")
                st.caption(f"数据类型：{group.iloc[0]['actual_budget']} | 摘要：{group.iloc[0]['summary']}")
            
            with col2:
                # 校验该凭证是否平衡
                is_balanced, errors = validateJournalEntries(group)
                if is_balanced:
                    st.success("✅ 借贷平衡")
                else:
                    st.error("❌ 借贷不平衡")
            
            # 显示分录明细
            display_data = group[[
                "account_code", "account_name",
                "debit_amount", "credit_amount"
            ]].copy()
            
            # 格式化金额
            display_data["借方金额"] = display_data["debit_amount"].apply(
                lambda x: f"{x:,.2f}" if pd.notna(x) else ""
            )
            display_data["贷方金额"] = display_data["credit_amount"].apply(
                lambda x: f"{x:,.2f}" if pd.notna(x) else ""
            )
            
            display_data = display_data.drop(columns=["debit_amount", "credit_amount"])
            display_data.columns = ["科目编码", "科目名称", "借方金额", "贷方金额"]
            
            st.dataframe(display_data, use_container_width=True, hide_index=True)


def _render_action_buttons(entries: pd.DataFrame, closing_enabled: bool) -> None:
    """渲染操作按钮
    
    Args:
        entries: 所有分录数据
        closing_enabled: 是否启用自动结转
    """
    if entries.empty:
        st.info("请先添加分录明细，然后生成凭证。")
        return
    
    # 校验是否平衡
    is_balanced, errors = validateJournalEntries(entries)
    
    if not is_balanced:
        st.error("分录不平衡，请先调整借方和贷方金额。")
        for error in errors:
            st.error(error)
        return
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 下载凭证", key="download", type="primary"):
            # 生成 Excel 文件
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                entries.to_excel(writer, index=False, sheet_name="序时账")
            
            output.seek(0)
            st.download_button(
                label="下载 Excel 文件",
                data=output,
                file_name=f"凭证_{st.session_state.period}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("➕ 添加至序时账", key="add_to_ledger", type="primary"):
            try:
                # 加载现有序时账
                existing_ledger = loadGeneralLedger()
                
                # 追加新分录
                new_ledger = pd.concat([existing_ledger, entries], ignore_index=True)
                
                # 保存序时账
                saveGeneralLedger(new_ledger)
                
                st.success(f"成功添加 {len(entries)} 条分录至序时账！")
                
                # 清空当前录入
                st.session_state.debit_entries = [{}]
                st.session_state.credit_entries = [{}]
                st.session_state.summary = ""
                st.rerun()
                
            except Exception as e:
                st.error(f"添加至序时账失败：{str(e)}")


def _render_template_management() -> None:
    """渲染模板管理"""
    st.markdown("---")
    st.markdown("### 分录模板")
    
    tab_save, tab_load = st.tabs(["保存模板", "加载模板"])
    
    with tab_save:
        # 检查是否有分录
        has_entries = (
            len(st.session_state.debit_entries) > 0 or 
            len(st.session_state.credit_entries) > 0
        )
        
        if not has_entries:
            st.info("当前没有分录，无法保存模板。")
            return
        
        template_name = st.text_input(
            "模板名称",
            placeholder="如：工资收入模板",
            key="template_name_input"
        )
        
        if st.button("💾 保存当前分录为模板", key="save_template"):
            if not template_name:
                st.error("请输入模板名称。")
                return
            
            try:
                template_data = {
                    "summary": st.session_state.summary,
                    "debit_entries": [
                        {
                            "account_code": entry.get("account_code"),
                            "account_name": entry.get("account_name"),
                            "amount": entry.get("amount", 0)
                        }
                        for entry in st.session_state.debit_entries
                        if "account_code" in entry
                    ],
                    "credit_entries": [
                        {
                            "account_code": entry.get("account_code"),
                            "account_name": entry.get("account_name"),
                            "amount": entry.get("amount", 0)
                        }
                        for entry in st.session_state.credit_entries
                        if "account_code" in entry
                    ]
                }
                
                saveJournalTemplate(template_name, template_data)
                st.success(f"模板「{template_name}」保存成功！")
                
            except Exception as e:
                st.error(f"保存模板失败：{str(e)}")
    
    with tab_load:
        try:
            # 加载模板列表
            templates_df = loadJournalTemplates()
            
            if templates_df.empty:
                st.info("暂无已保存的模板。")
                return
            
            # 显示模板列表
            for _, row in templates_df.iterrows():
                col1, col2, col3 = st.columns([4, 2, 2])
                
                with col1:
                    st.write(f"**{row['模板名称']}**")
                    st.caption(f"创建时间：{row['创建时间']}")
                
                with col2:
                    if st.button("📂 加载", key=f"load_template_{row['模板ID']}"):
                        try:
                            template_data = getJournalTemplate(row['模板ID'])
                            
                            # 加载模板数据
                            st.session_state.summary = template_data.get("summary", "")
                            
                            # 加载借方科目
                            st.session_state.debit_entries = []
                            for debit_entry in template_data.get("debit_entries", []):
                                if debit_entry.get("account_code"):
                                    st.session_state.debit_entries.append(debit_entry)
                            
                            # 如果没有借方科目，添加一个空行
                            if not st.session_state.debit_entries:
                                st.session_state.debit_entries = [{}]
                            
                            # 加载贷方科目
                            st.session_state.credit_entries = []
                            for credit_entry in template_data.get("credit_entries", []):
                                if credit_entry.get("account_code"):
                                    st.session_state.credit_entries.append(credit_entry)
                            
                            # 如果没有贷方科目，添加一个空行
                            if not st.session_state.credit_entries:
                                st.session_state.credit_entries = [{}]
                            
                            st.success(f"模板「{row['模板名称']}」加载成功！")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"加载模板失败：{str(e)}")
                
                with col3:
                    if st.button("🗑️ 删除", key=f"delete_template_{row['模板ID']}"):
                        try:
                            deleteJournalTemplate(row['模板ID'])
                            st.success(f"模板「{row['模板名称']}」删除成功！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"删除模板失败：{str(e)}")
                
                st.markdown("---")
                
        except Exception as e:
            st.error(f"加载模板列表失败：{str(e)}")