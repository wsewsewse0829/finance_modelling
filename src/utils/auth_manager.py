"""
认证管理模块
处理用户登录、注册、登出等认证相关功能
"""

import os
from supabase import create_client, Client
import streamlit as st
from typing import Optional

# 从环境变量或 Streamlit secrets 获取 Supabase 凭证
# 本地开发环境使用环境变量，Streamlit Cloud 使用 secrets
SUPABASE_URL = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", ""))
SUPABASE_KEY = os.getenv("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", ""))

# 创建 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_current_user() -> Optional[dict]:
    """获取当前登录用户"""
    try:
        # 从 session 获取用户信息
        if 'user_id' in st.session_state and st.session_state.user_id:
            return {
                'id': st.session_state.user_id,
                'email': st.session_state.get('user_email', '')
            }
        return None
    except Exception as e:
        st.error(f"获取用户信息失败: {str(e)}")
        return None


def login(email: str, password: str) -> bool:
    """用户登录
    
    Args:
        email: 用户邮箱
        password: 用户密码
        
    Returns:
        bool: 登录是否成功
    """
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # 保存用户信息到 session
            st.session_state.user_id = str(response.user.id)
            st.session_state.user_email = response.user.email
            st.session_state.access_token = response.session.access_token
            
            st.success(f"欢迎回来，{response.user.email}！")
            return True
        else:
            st.error("登录失败：邮箱或密码错误")
            return False
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            st.error("登录失败：邮箱或密码错误")
        elif "Email not confirmed" in error_msg:
            st.error("登录失败：请先验证邮箱")
        else:
            st.error(f"登录失败: {error_msg}")
        return False


def register(email: str, password: str) -> bool:
    """用户注册
    
    Args:
        email: 用户邮箱
        password: 用户密码
        
    Returns:
        bool: 注册是否成功
    """
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            st.success("🎉 注册成功！")
            st.info("📧 请检查您的邮箱，点击验证链接完成注册。")
            st.info("验证后即可登录使用系统。")
            return True
        else:
            st.error("注册失败，请稍后重试")
            return False
    except Exception as e:
        error_msg = str(e)
        if "User already registered" in error_msg:
            st.error("注册失败：该邮箱已被注册")
        elif "Password should be at least 6 characters" in error_msg:
            st.error("注册失败：密码至少需要 6 个字符")
        elif "Unable to validate email address" in error_msg:
            st.error("注册失败：邮箱格式不正确")
        else:
            st.error(f"注册失败: {error_msg}")
        return False


def logout() -> None:
    """用户登出"""
    try:
        supabase.auth.sign_out()
        
        # 清除 session 中的用户信息
        keys_to_clear = ['user_id', 'user_email', 'access_token']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # 清除其他缓存数据
        if 'accounts_data' in st.session_state:
            del st.session_state.accounts_data
        if 'ledger_data' in st.session_state:
            del st.session_state.ledger_data
        
        st.success("✅ 已成功登出")
        st.rerun()
    except Exception as e:
        st.error(f"登出失败: {str(e)}")


def check_auth() -> bool:
    """检查用户是否已登录
    
    Returns:
        bool: 用户是否已登录
    """
    return 'user_id' in st.session_state and st.session_state.user_id is not None


def require_auth() -> None:
    """要求用户登录，如果未登录则跳转到登录页"""
    if not check_auth():
        st.warning("🔐 请先登录")
        st.info("点击下方按钮前往登录页面")
        if st.button("前往登录", key="require_auth_login"):
            st.switch_page("src/pages/login.py")
        st.stop()


def get_user_id() -> str:
    """获取当前用户 ID
    
    Returns:
        str: 用户 ID
        
    Raises:
        Exception: 用户未登录时抛出异常
    """
    if not check_auth():
        raise Exception("用户未登录")
    return st.session_state.user_id


def is_authenticated() -> bool:
    """检查用户是否已认证（别名函数）"""
    return check_auth()


def refresh_session() -> bool:
    """刷新用户 session
    
    Returns:
        bool: 刷新是否成功
    """
    try:
        if 'access_token' in st.session_state:
            response = supabase.auth.get_session()
            if response:
                st.session_state.access_token = response.access_token
                return True
        return False
    except Exception:
        return False