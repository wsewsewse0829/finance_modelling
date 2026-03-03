"""
个人财务规划应用 - 主程序入口
基于 Streamlit 的个人财务管理应用
"""

import streamlit as st
import os

# 导入认证模块
from src.utils.auth_manager import check_auth, logout, get_current_user, login, register

# 导入页面组件
from src.components.sidebar import (
    renderSidebar,
    PAGE_HOME,
    PAGE_FINANCIAL_STATEMENTS,
    PAGE_BUDGET_ANALYSIS,
    PAGE_ACCOUNT_MANAGEMENT,
    PAGE_DATA_UPLOAD,
)
from src.pages.home import renderHomePage
from src.pages.financial_statements import renderFinancialStatementsPage
from src.pages.budget_analysis import renderBudgetAnalysisPage
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

    # 检查用户是否已登录
    if not check_auth():
        # 显示登录/注册页面
        _renderAuthPage()
        st.stop()

    # 获取当前用户信息
    current_user = get_current_user()
    if current_user:
        # 在侧边栏顶部显示用户信息
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 用户信息")
            st.info(f"📧 {current_user['email']}")
            
            # 添加登出按钮
            if st.button("🚪 登出", use_container_width=True):
                logout()

    # 渲染侧边栏并获取当前页面
    selected_page = renderSidebar()

    # 根据选择的页面路由到对应的功能
    if selected_page == PAGE_HOME:
        renderHomePage()
    elif selected_page == PAGE_FINANCIAL_STATEMENTS:
        renderFinancialStatementsPage()
    elif selected_page == PAGE_BUDGET_ANALYSIS:
        renderBudgetAnalysisPage()
    elif selected_page == PAGE_ACCOUNT_MANAGEMENT:
        renderAccountManagementPage()
    elif selected_page == PAGE_DATA_UPLOAD:
        renderDataUploadPage()
    else:
        renderHomePage()  # 默认首页


def _renderAuthPage():
    """渲染登录/注册页面"""
    
    # 标题
    st.title("🔐 用户认证")
    st.markdown("---")
    
    # 标签页
    tab_login, tab_register = st.tabs(["🔑 登录", "📝 注册"])
    
    # 登录表单
    with tab_login:
        st.subheader("登录您的账户")
        
        with st.form("login_form"):
            email = st.text_input("邮箱地址", placeholder="your@email.com", key="login_email")
            password = st.text_input("密码", type="password", key="login_password")
            
            submitted = st.form_submit_button("登录", type="primary", use_container_width=True)
            
            if submitted:
                if not email:
                    st.error("请输入邮箱地址")
                elif not password:
                    st.error("请输入密码")
                else:
                    if login(email, password):
                        # 登录成功，重新加载页面
                        st.rerun()
        
        st.markdown("---")
        st.info("💡 首次使用？请切换到「注册」标签页创建账号。")
    
    # 注册表单
    with tab_register:
        st.subheader("创建新账户")
        
        with st.form("register_form"):
            reg_email = st.text_input("邮箱地址", placeholder="your@email.com", key="reg_email")
            reg_password = st.text_input("密码", type="password", key="reg_password", help="密码至少需要 6 个字符")
            confirm_password = st.text_input("确认密码", type="password", key="confirm_password")
            
            submitted = st.form_submit_button("注册", type="primary", use_container_width=True)
            
            if submitted:
                if not reg_email:
                    st.error("请输入邮箱地址")
                elif not reg_password:
                    st.error("请输入密码")
                elif not confirm_password:
                    st.error("请确认密码")
                elif reg_password != confirm_password:
                    st.error("两次输入的密码不一致")
                elif len(reg_password) < 6:
                    st.error("密码至少需要 6 个字符")
                else:
                    if register(reg_email, reg_password):
                        st.info("注册成功！请切换到「登录」标签页进行登录。")
        
        st.markdown("---")
        st.info("📧 注册后需要验证邮箱，验证完成后即可登录使用系统。")


if __name__ == "__main__":
    main()
