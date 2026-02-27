"""
科目管理页面
用户自定义管理科目表，支持增删改查
"""

import streamlit as st
import pandas as pd

from src.utils.data_manager import loadAccounts, saveAccounts
from src.types.models import ACCOUNT_TYPES


def renderAccountManagementPage() -> None:
    """渲染科目管理页面"""
    st.title("📋 科目管理")
    st.markdown("---")

    # 加载科目数据
    accounts = loadAccounts()

    # 标签页：查看科目 / 添加科目
    tab_view, tab_add = st.tabs(["查看科目表", "添加科目"])

    with tab_view:
        _renderAccountTable(accounts)

    with tab_add:
        _renderAddAccountForm(accounts)


def _renderAccountTable(accounts: pd.DataFrame) -> None:
    """渲染科目表展示"""
    st.subheader("当前科目表")

    if accounts.empty:
        st.info("暂无科目数据。")
        return

    # 按科目类型筛选
    account_types = ["全部"] + ACCOUNT_TYPES
    selected_type = st.selectbox("按科目类型筛选", account_types)

    if selected_type != "全部":
        filtered = accounts[accounts["account_type"] == selected_type]
    else:
        filtered = accounts

    # 展示科目表
    st.dataframe(
        filtered[["account_code", "account_name", "account_type", "parent_code", "balance_direction"]].rename(
            columns={
                "account_code": "科目编码",
                "account_name": "科目名称",
                "account_type": "科目类型",
                "parent_code": "父科目编码",
                "balance_direction": "余额方向",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(f"共 {len(filtered)} 个科目")

    # 删除科目功能
    st.markdown("---")
    st.subheader("删除科目")
    delete_code = st.selectbox(
        "选择要删除的科目",
        accounts["account_code"].tolist(),
        format_func=lambda x: f"{x} - {accounts[accounts['account_code'] == x]['account_name'].values[0]}",
    )

    if st.button("🗑️ 删除选中科目", type="secondary"):
        updated = accounts[accounts["account_code"] != delete_code]
        saveAccounts(updated)
        st.success(f"已删除科目: {delete_code}")
        st.rerun()


def _renderAddAccountForm(accounts: pd.DataFrame) -> None:
    """渲染添加科目表单"""
    st.subheader("添加新科目")

    with st.form("add_account_form"):
        col1, col2 = st.columns(2)

        with col1:
            account_code = st.text_input("科目编码", placeholder="例如: 1003")
            account_name = st.text_input("科目名称", placeholder="例如: 微信钱包")
            account_type = st.selectbox("科目类型", ACCOUNT_TYPES)

        with col2:
            # 父科目选择（可选）
            parent_options = ["无（一级科目）"] + [
                f"{row['account_code']} - {row['account_name']}"
                for _, row in accounts.iterrows()
            ]
            parent_selection = st.selectbox("父科目", parent_options)
            balance_direction = st.selectbox("余额方向", ["借", "贷"])

        submitted = st.form_submit_button("➕ 添加科目", type="primary")

        if submitted:
            # 校验
            if not account_code or not account_name:
                st.error("科目编码和科目名称不能为空。")
                return

            if account_code in accounts["account_code"].values:
                st.error(f"科目编码 {account_code} 已存在。")
                return

            # 解析父科目编码
            parent_code = ""
            if parent_selection != "无（一级科目）":
                parent_code = parent_selection.split(" - ")[0]

            # 添加新科目
            new_account = pd.DataFrame([{
                "account_code": account_code,
                "account_name": account_name,
                "account_type": account_type,
                "parent_code": parent_code,
                "balance_direction": balance_direction,
            }])

            updated = pd.concat([accounts, new_account], ignore_index=True)
            saveAccounts(updated)
            st.success(f"已添加科目: {account_code} - {account_name}")
            st.rerun()
