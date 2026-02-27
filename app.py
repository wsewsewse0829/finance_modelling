"""
个人财务规划应用 - 主程序入口
基于 Streamlit 的个人财务管理应用
"""

import streamlit as st
import os

# 导入页面组件
from src.components.sidebar import (
    renderSidebar,
    PAGE_HOME,
    PAGE_FINANCIAL_STATEMENTS,
    PAGE_ACCOUNT_MANAGEMENT,
    PAGE_DATA_UPLOAD,
)
from src.pages.home import renderHomePage
from src.pages.financial_statements import renderFinancialStatementsPage
from src.pages.account_management import renderAccountManagementPage
from src.pages.data_upload import renderDataUploadPage

# 页面配置
st.set_page_config(
    page_title="个人财务规划",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """主函数 - 应用路由控制"""

    # 渲染侧边栏并获取当前页面
    selected_page = renderSidebar()

    # 根据选择的页面路由到对应的功能
    if selected_page == PAGE_HOME:
        renderHomePage()
    elif selected_page == PAGE_FINANCIAL_STATEMENTS:
        renderFinancialStatementsPage()
    elif selected_page == PAGE_ACCOUNT_MANAGEMENT:
        renderAccountManagementPage()
    elif selected_page == PAGE_DATA_UPLOAD:
        renderDataUploadPage()
    else:
        renderHomePage()  # 默认首页


if __name__ == "__main__":
    main()