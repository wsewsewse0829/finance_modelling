"""
登录/注册页面
"""

import streamlit as st
from src.utils.auth_manager import login, register, check_auth, diagnose_supabase


def renderLoginPage():
    """渲染登录/注册页面"""
    
    # 设置页面配置
    st.set_page_config(
        page_title="登录 - 财务建模",
        page_icon="🔐",
        layout="centered"
    )
    
    # 如果已登录，跳转到首页
    if check_auth():
        st.switch_page("home.py")
    
    # 标题
    st.title("🔐 用户认证")
    
    # 诊断按钮
    with st.expander("🔍 诊断 Supabase 配置"):
        if st.button("运行诊断", key="diagnose_button"):
            with st.spinner("正在诊断 Supabase 配置..."):
                results = diagnose_supabase()
                
                st.subheader("📊 诊断结果")
                
                # 显示结果
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("URL 已配置", "✅ 是" if results["url_configured"] else "❌ 否")
                    st.metric("Key 已配置", "✅ 是" if results["key_configured"] else "❌ 否")
                    st.metric("URL 可访问", "✅ 是" if results.get("url_accessible", False) else "❌ 否")
                
                with col2:
                    st.metric("API Key 有效", "✅ 是" if results.get("api_key_valid", False) else "❌ 否")
                    st.metric("认证端点可访问", "✅ 是" if results.get("auth_endpoint_accessible", False) else "❌ 否")
                    st.metric("登录端点可访问", "✅ 是" if results.get("login_endpoint_accessible", False) else "❌ 否")
                
                # 显示错误
                if results["errors"]:
                    st.error("❌ 发现以下问题：")
                    for error in results["errors"]:
                        st.error(f"• {error}")
                else:
                    st.success("✅ 所有检查通过！Supabase 配置正常。")
    
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
                        # 登录成功，跳转到首页
                        st.success("登录成功！正在跳转...")
                        st.switch_page("home.py")
        
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
                        st.info("注册成功后请切换到「登录」标签页进行登录")
        
        st.markdown("---")
        st.info("📧 注册后需要验证邮箱，验证完成后即可登录使用系统。")


# 渲染页面
if __name__ == "__main__":
    renderLoginPage()