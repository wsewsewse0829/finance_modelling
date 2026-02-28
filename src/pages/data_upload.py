"""
数据上传页面
用户上传序时账数据，系统自动校验并生成科目余额表和会计报表
"""

import streamlit as st
import pandas as pd
from io import StringIO
import os
from datetime import datetime

from src.utils.data_manager import (
    loadGeneralLedger, saveGeneralLedger,
    loadAccounts, saveTrialBalance, saveReport,
    getWorkingPapersList, saveWorkingPaper, deleteWorkingPaper, getWorkingPaperPath,
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
    tab_upload, tab_view, tab_template, tab_working_papers = st.tabs(["上传数据", "查看序时账", "下载模板", "工作底稿"])

    with tab_upload:
        _renderUploadSection()

    with tab_view:
        _renderLedgerView()

    with tab_template:
        _renderTemplateDownload()

    with tab_working_papers:
        _renderWorkingPapers()


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
            # 统一日期格式为 YYYY-MM-DD 字符串
            df["entry_date"] = pd.to_datetime(df["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
            # 过滤掉日期转换失败的记录
            df = df[df["entry_date"].notna()]

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
    col1, col2 = st.columns(2)
    
    with col1:
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
    
    with col2:
        # 按会计期间删除
        st.markdown("#### 按会计期间删除")
        
        try:
            # 提取会计期间
            # 现在日期列已经是字符串格式 (YYYY-MM-DD)
            ledger_copy = ledger.copy()
            
            # 从日期字符串中提取期间 (YYYY-MM)
            ledger_copy["period"] = ledger_copy["entry_date"].str.slice(0, 7)
            
            # 过滤掉无效期间
            ledger_copy = ledger_copy[ledger_copy["period"].notna() & (ledger_copy["period"] != "")]
            
            if not ledger_copy.empty:
                periods = sorted(ledger_copy["period"].unique())
                
                if periods:
                    selected_period = st.selectbox("选择要删除的会计期间", periods, key="delete_period")
                    if st.button("🗑️ 删除选中期间数据", type="secondary", key="delete_period_btn"):
                        # 删除选定期间的数据
                        # 同样使用字符串提取期间
                        ledger_for_filter = ledger.copy()
                        ledger_for_filter["period"] = ledger_for_filter["entry_date"].str.slice(0, 7)
                        
                        filtered_ledger = ledger_for_filter[ledger_for_filter["period"] != selected_period].copy()
                        # 移除临时列
                        filtered_ledger = filtered_ledger.drop(columns=["period"])
                        
                        # 保存过滤后的序时账
                        saveGeneralLedger(filtered_ledger)
                        
                        # 重新生成科目余额表和会计报表
                        accounts = loadAccounts()
                        if not filtered_ledger.empty:
                            trial_balance = generateTrialBalance(filtered_ledger, accounts)
                            saveTrialBalance(trial_balance)
                            report = generateReport(trial_balance, accounts)
                            saveReport(report)
                        else:
                            # 如果没有数据，清空报表
                            saveTrialBalance(pd.DataFrame(columns=[
                                "account_code", "account_name", "period",
                                "begin_balance", "debit_total", "credit_total", "end_balance"
                            ]))
                            saveReport(pd.DataFrame(columns=["item", "period", "amount", "report_type"]))
                        
                        st.success(f"已删除 {selected_period} 期间的数据。")
                        st.rerun()
                else:
                    st.info("暂无有效的会计期间数据。")
            else:
                st.info("暂无有效的日期数据。")
        except Exception as e:
            st.error(f"加载期间数据失败: {str(e)}")


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


def _renderWorkingPapers() -> None:
    """渲染工作底稿管理"""
    st.subheader("工作底稿管理")
    st.markdown("上传、下载和删除线下制作的工作底稿文件。")

    # 获取工作底稿列表
    working_papers = getWorkingPapersList()

    st.markdown("---")

    # 上传区域
    st.markdown("#### 📤 上传工作底稿")
    uploaded_file = st.file_uploader(
        "选择工作底稿文件",
        type=["csv", "xlsx", "xls"],
        help="支持 CSV 和 Excel 格式",
        key="working_papers_upload"
    )

    # 显示文件信息
    if uploaded_file is not None:
        st.info(f"已选择文件: {uploaded_file.name} ({len(uploaded_file.getbuffer()) / 1024:.2f} KB)")
        
        # 确认上传按钮
        if st.button("📥 确认上传", type="primary", key="upload_working_paper"):
            try:
                # 生成唯一文件名
                file_ext = os.path.splitext(uploaded_file.name)[1]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"working_paper_{timestamp}{file_ext}"
                
                # 保存文件
                file_path = getWorkingPaperPath(unique_filename)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 保存元数据
                file_size = len(uploaded_file.getbuffer())
                upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                saveWorkingPaper(unique_filename, upload_date, file_size)
                
                st.success(f"✅ 工作底稿上传成功！")
                st.balloons()
                st.rerun()
                
            except Exception as e:
                st.error(f"上传失败: {str(e)}")

    st.markdown("---")

    # 显示工作底稿列表
    st.markdown("#### 📋 工作底稿列表")

    if working_papers.empty:
        st.info("暂无工作底稿。请上传文件。")
        return

    # 显示统计信息
    col1, col2 = st.columns(2)
    with col1:
        st.metric("文件数量", len(working_papers))
    with col2:
        total_size = working_papers["file_size"].sum()
        st.metric("总大小", f"{total_size / 1024:.2f} KB")

    st.markdown("---")

    # 显示文件列表
    for idx, row in working_papers.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.markdown(f"**{row['filename']}**")
                st.caption(f"上传时间: {row['upload_date']}")
            
            with col2:
                # 下载按钮
                file_path = getWorkingPaperPath(row['filename'])
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    
                    st.download_button(
                        label="📥 下载",
                        data=file_data,
                        file_name=row['filename'],
                        key=f"download_{idx}",
                        use_container_width=True
                    )
                else:
                    st.warning("文件不存在")
            
            with col3:
                # 删除按钮
                if st.button("🗑️ 删除", key=f"delete_{idx}"):
                    if deleteWorkingPaper(row['filename']):
                        st.success("删除成功！")
                        st.rerun()
                    else:
                        st.error("删除失败！")
            
            st.markdown("---")

    st.markdown("""
    💡 **提示**：
    - 工作底稿用于存储线下制作的辅助计算文件
    - 下载格式与上传格式保持一致
    - 删除工作底稿不会影响序时账和会计报表数据
    """)
