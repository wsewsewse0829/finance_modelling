"""
数据上传页面
用户上传序时账数据，系统自动校验并生成科目余额表和会计报表
"""

import streamlit as st
import pandas as pd
from io import StringIO

from src.utils.data_manager import (
    loadGeneralLedger, saveGeneralLedger,
    loadAccounts, saveTrialBalance, saveReport,
)
from src.utils.accounting import (
    validateJournalEntries, generateTrialBalance, generateReport,
)


# 序时账必需列
REQUIRED_COLUMNS = [
    "entry_date", "voucher_no", "account_code",
    "account_name", "debit_amount", "credit_amount",
]


def renderDataUploadPage() -> None:
    """渲染数据上传页面"""
    st.title("📤 数据上传")
    st.markdown("---")

    # 标签页
    tab_upload, tab_view, tab_template = st.tabs(["上传数据", "查看序时账", "下载模板"])

    with tab_upload:
        _renderUploadSection()

    with tab_view:
        _renderLedgerView()

    with tab_template:
        _renderTemplateDownload()


def _renderUploadSection() -> None:
    """渲染上传区域"""
    st.subheader("上传序时账")
    st.markdown("请上传 CSV 或 Excel 格式的序时账文件。")

    uploaded_file = st.file_uploader(
        "选择文件",
        type=["csv", "xlsx", "xls"],
        help="支持 CSV 和 Excel 格式",
    )

    if uploaded_file is not None:
        try:
            # 读取文件
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.success(f"文件读取成功，共 {len(df)} 条记录。")

            # 显示预览
            st.markdown("#### 数据预览")
            st.dataframe(df.head(10), use_container_width=True)

            # 校验列名
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                st.error(f"缺少必需列: {', '.join(missing_cols)}")
                st.markdown("**必需列：** " + ", ".join(REQUIRED_COLUMNS))
                return

            # 数据类型转换
            df["debit_amount"] = pd.to_numeric(df["debit_amount"], errors="coerce").fillna(0)
            df["credit_amount"] = pd.to_numeric(df["credit_amount"], errors="coerce").fillna(0)
            df["account_code"] = df["account_code"].astype(str)

            # 添加缺失列
            if "id" not in df.columns:
                existing = loadGeneralLedger()
                start_id = len(existing) + 1
                df["id"] = range(start_id, start_id + len(df))
            if "summary" not in df.columns:
                df["summary"] = ""
            if "user_id" not in df.columns:
                df["user_id"] = 1

            # 借贷平衡校验
            st.markdown("#### 借贷平衡校验")
            is_balanced, errors = validateJournalEntries(df)

            if is_balanced:
                st.success("✅ 所有分录借贷平衡！")
            else:
                st.error("❌ 存在借贷不平衡的分录：")
                for error in errors:
                    st.warning(error)

            # 确认上传
            upload_mode = st.radio(
                "上传模式",
                ["追加到现有数据", "替换现有数据"],
                horizontal=True,
            )

            if st.button("📥 确认上传", type="primary"):
                _processUpload(df, upload_mode)

        except Exception as e:
            st.error(f"文件读取失败: {str(e)}")


def _processUpload(new_data: pd.DataFrame, upload_mode: str) -> None:
    """处理数据上传"""
    accounts = loadAccounts()

    if upload_mode == "追加到现有数据":
        existing = loadGeneralLedger()
        combined = pd.concat([existing, new_data], ignore_index=True)
    else:
        combined = new_data

    # 保存序时账
    saveGeneralLedger(combined)

    # 自动生成科目余额表
    trial_balance = generateTrialBalance(combined, accounts)
    saveTrialBalance(trial_balance)

    # 自动生成会计报表
    report = generateReport(trial_balance, accounts)
    saveReport(report)

    st.success("✅ 数据上传成功！已自动生成科目余额表和会计报表。")
    st.info("请前往「会计报表」页面查看生成的报表。")


def _renderLedgerView() -> None:
    """渲染序时账查看"""
    st.subheader("当前序时账数据")

    ledger = loadGeneralLedger()

    if ledger.empty:
        st.info("暂无序时账数据。请先上传数据。")
        return

    # 显示统计信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总记录数", len(ledger))
    with col2:
        st.metric("分录数", ledger["voucher_no"].nunique())
    with col3:
        total_debit = ledger["debit_amount"].sum()
        st.metric("借方总额", f"{total_debit:,.2f}")

    st.markdown("---")

    # 显示数据表
    display_df = ledger.rename(columns={
        "id": "ID",
        "entry_date": "日期",
        "voucher_no": "分录号",
        "account_code": "科目编码",
        "account_name": "科目名称",
        "debit_amount": "借方金额",
        "credit_amount": "贷方金额",
        "summary": "摘要",
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # 清空数据按钮
    st.markdown("---")
    if st.button("🗑️ 清空所有序时账数据", type="secondary"):
        saveGeneralLedger(pd.DataFrame(columns=[
            "id", "entry_date", "voucher_no", "account_code",
            "account_name", "debit_amount", "credit_amount", "summary", "user_id"
        ]))
        saveTrialBalance(pd.DataFrame(columns=[
            "account_code", "account_name", "period",
            "begin_balance", "debit_total", "credit_total", "end_balance"
        ]))
        saveReport(pd.DataFrame(columns=["item", "period", "amount", "report_type"]))
        st.success("已清空所有数据。")
        st.rerun()


def _renderTemplateDownload() -> None:
    """渲染模板下载"""
    st.subheader("下载序时账模板")
    st.markdown("请按照以下格式准备您的序时账数据：")

    # 模板数据
    template_data = {
        "entry_date": ["2024-01-01", "2024-01-01", "2024-01-15", "2024-01-15"],
        "voucher_no": ["JV-001", "JV-001", "JV-002", "JV-002"],
        "account_code": ["1002", "4001", "5001", "1002"],
        "account_name": ["银行存款", "工资收入", "生活费用", "银行存款"],
        "debit_amount": [10000.00, 0.00, 3000.00, 0.00],
        "credit_amount": [0.00, 10000.00, 0.00, 3000.00],
        "summary": ["收到工资", "收到工资", "支付房租", "支付房租"],
    }

    template_df = pd.DataFrame(template_data)
    st.dataframe(template_df, use_container_width=True, hide_index=True)

    # 下载按钮
    csv_data = template_df.to_csv(index=False)
    st.download_button(
        label="📥 下载 CSV 模板",
        data=csv_data,
        file_name="journal_entry_template.csv",
        mime="text/csv",
    )

    st.markdown("""
    #### 字段说明
    | 字段名 | 说明 | 必填 |
    |--------|------|------|
    | entry_date | 会计日期（YYYY-MM-DD） | ✅ |
    | voucher_no | 分录号 | ✅ |
    | account_code | 科目编码 | ✅ |
    | account_name | 科目名称 | ✅ |
    | debit_amount | 借方金额 | ✅ |
    | credit_amount | 贷方金额 | ✅ |
    | summary | 摘要 | ❌ |
    """)
