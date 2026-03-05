"""
侧边栏导航组件
提供页面切换功能
"""

import streamlit as st


# 页面配置常量
PAGE_HOME = "🏠 首页"
PAGE_JOURNAL_ENTRY = "📝 手动录入分录"
PAGE_FINANCIAL_STATEMENTS = "📊 会计报表"
PAGE_BUDGET_ANALYSIS = "📈 预实分析"
PAGE_ACCOUNT_MANAGEMENT = "📋 科目管理"
PAGE_DATA_UPLOAD = "📤 数据上传"

PAGES = [
    PAGE_HOME,
    PAGE_JOURNAL_ENTRY,
    PAGE_FINANCIAL_STATEMENTS,
    PAGE_BUDGET_ANALYSIS,
    PAGE_ACCOUNT_MANAGEMENT,
    PAGE_DATA_UPLOAD,
]


def renderSidebar() -> str:
    """
    渲染侧边栏导航，返回当前选中的页面名称
    """
    with st.sidebar:
        st.title("💰 个人财务规划")
        st.markdown("---")

        selected_page = st.radio(
            "页面导航",
            PAGES,
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.caption("v0.1.0 MVP")
        st.caption("采用企业财务管理思维")
        st.caption("管理个人财务")

    return selected_page
