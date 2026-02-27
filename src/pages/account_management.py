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

    # 标签页：查看科目 / 添加科目 / 批量上传
    tab_view, tab_add, tab_batch = st.tabs(["查看科目表", "添加科目", "批量上传"])

    with tab_view:
        _renderAccountTable(accounts)

    with tab_add:
        _renderAddAccountForm(accounts)

    with tab_batch:
        _renderBatchUpload(accounts)


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


def _renderBatchUpload(accounts: pd.DataFrame) -> None:
    """渲染批量上传科目"""
    st.subheader("批量上传科目")
    
    # 1. 下载模板
    st.markdown("### 📥 第一步：下载模板")
    st.markdown("下载科目上传模板，按照模板格式填写数据后上传。")
    
    template_data = {
        "科目编码": ["1001", "1002", "3001", "4001", "5001"],
        "科目名称": ["现金", "银行存款", "实收资本", "工资收入", "生活费用"],
        "科目类型": ["资产", "资产", "所有者权益", "收入", "费用"],
        "父科目编码": ["", "", "", "", ""],
        "余额方向": ["借", "借", "贷", "贷", "借"],
    }
    template_df = pd.DataFrame(template_data)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**模板格式说明：**")
        st.markdown("- 科目编码：科目编码，不限制长度，例如 1001 或 100101")
        st.markdown("- 科目名称：科目名称，不能为空")
        st.markdown("- 科目类型：资产/负债/所有者权益/收入/费用")
        st.markdown("- 父科目编码：如果是一级科目，留空")
        st.markdown("- 余额方向：借/贷")
    
    with col2:
        if st.button("⬇️ 下载科目模板"):
            csv = template_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下载模板文件",
                data=csv,
                file_name="科目模板.csv",
                mime="text/csv",
            )
    
    # 2. 上传文件
    st.markdown("---")
    st.markdown("### 📤 第二步：上传数据")
    uploaded_file = st.file_uploader(
        "上传科目文件",
        type=['csv', 'xlsx'],
        help="支持CSV或Excel文件，请确保格式与模板一致"
    )
    
    if uploaded_file is not None:
        # 读取文件
        try:
            if uploaded_file.name.endswith('.csv'):
                new_accounts = pd.read_csv(uploaded_file)
            else:
                new_accounts = pd.read_excel(uploaded_file)
            
            # 数据校验
            required_columns = ["科目编码", "科目名称", "科目类型", "余额方向"]
            missing_cols = [col for col in required_columns if col not in new_accounts.columns]
            
            if missing_cols:
                st.error(f"文件缺少必要列: {', '.join(missing_cols)}")
                return
            
            # 重命名列名以匹配数据库
            column_mapping = {
                "科目编码": "account_code",
                "科目名称": "account_name",
                "科目类型": "account_type",
                "父科目编码": "parent_code",
                "余额方向": "balance_direction"
            }
            new_accounts = new_accounts.rename(columns=column_mapping)
            
            # 确保科目编码为字符串类型
            new_accounts["account_code"] = new_accounts["account_code"].astype(str)
            
            # 处理父科目编码（将"无"或空值转为空字符串）
            if "parent_code" in new_accounts.columns:
                new_accounts["parent_code"] = new_accounts["parent_code"].fillna("")
                new_accounts["parent_code"] = new_accounts["parent_code"].apply(
                    lambda x: "" if str(x).strip() in ["无", "nan", "None", ""] else str(x)
                )
            else:
                new_accounts["parent_code"] = ""
            
            # 验证科目类型
            valid_types = ACCOUNT_TYPES
            invalid_types = new_accounts[~new_accounts["account_type"].isin(valid_types)]
            if not invalid_types.empty:
                st.error(f"无效的科目类型: {invalid_types['account_type'].unique().tolist()}")
                return
            
            # 检查科目编码是否已存在
            existing_codes = set(accounts["account_code"].astype(str).values)
            duplicate_codes = set(new_accounts["account_code"].astype(str).values) & existing_codes
            
            if duplicate_codes:
                st.warning(f"以下科目编码已存在，将被跳过: {duplicate_codes}")
                new_accounts = new_accounts[~new_accounts["account_code"].isin(duplicate_codes)]
            
            # 预览数据
            st.markdown("### 📋 数据预览")
            st.dataframe(
                new_accounts.rename(columns={
                    "account_code": "科目编码",
                    "account_name": "科目名称",
                    "account_type": "科目类型",
                    "parent_code": "父科目编码",
                    "balance_direction": "余额方向"
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # 确认上传
            if st.button("✅ 确认上传", type="primary", key="confirm_upload"):
                # 合并数据
                updated = pd.concat([accounts, new_accounts], ignore_index=True)
                saveAccounts(updated)
                st.success(f"成功上传 {len(new_accounts)} 个科目！")
                st.rerun()
        
        except Exception as e:
            st.error(f"上传失败: {str(e)}")
            st.markdown("请检查文件格式是否正确。")
    
    # 3. 上传提示
    st.markdown("---")
    st.info("💡 **提示：**")
    st.markdown("- 批量上传会跳过已存在的科目编码")
    st.markdown("- 上传前请确保数据格式正确，避免重复科目")
    st.markdown("- 父科目编码可以留空表示一级科目")
