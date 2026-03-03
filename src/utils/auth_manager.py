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
def _get_supabase_credentials():
    """获取 Supabase 凭证"""
    # 尝试从环境变量获取
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    
    # 如果环境变量中没有，尝试从 st.secrets 获取
    if not url or not key:
        try:
            if not url:
                url = st.secrets.get("SUPABASE_URL", "")
            if not key:
                key = st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            # st.secrets 可能还未初始化
            pass
    
    return url, key

# 创建 Supabase 客户端（延迟初始化）
supabase: Client = None

def _init_supabase_client():
    """初始化 Supabase 客户端"""
    global supabase
    if supabase is None:
        url, key = _get_supabase_credentials()
        if url and key:
            try:
                supabase = create_client(url, key)
                # 验证客户端是否正确创建
                if supabase is not None:
                    if not hasattr(supabase, 'auth'):
                        st.error("❌ Supabase 客户端创建失败：缺少 auth 属性")
                        return None
            except Exception as e:
                st.error(f"❌ 创建 Supabase 客户端时出错: {str(e)}")
                return None
    return supabase


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
    # 调试信息
    url, key = _get_supabase_credentials()
    st.write(f"调试: URL 是否存在: {bool(url)}")
    st.write(f"调试: Key 是否存在: {bool(key)}")
    
    client = _init_supabase_client()
    st.write(f"调试: 客户端是否初始化: {client is not None}")
    
    if client is None:
        st.error("❌ Supabase 客户端未正确初始化，请检查配置")
        return False
    
    try:
        st.write("调试: 尝试登录...")
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.write(f"调试: 登录响应: {response}")
        
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
    client = _init_supabase_client()
    if client is None:
        st.error("❌ Supabase 客户端未正确初始化，请检查配置")
        return False
    
    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "email_confirm": True  # 自动确认邮箱，无需邮件验证
            }
        })
        
        if response.user:
            st.success("🎉 注册成功！")
            st.info("✅ 您的账户已创建，可以直接登录使用系统。")
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
    client = _init_supabase_client()
    if client is None:
        st.warning("⚠️ Supabase 客户端未初始化")
        # 仍然清除 session
        keys_to_clear = ['user_id', 'user_email', 'access_token']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
        return
    
    try:
        client.auth.sign_out()
        
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
        client = _init_supabase_client()
        if client and 'access_token' in st.session_state:
            response = client.auth.get_session()
            if response:
                st.session_state.access_token = response.access_token
                return True
        return False
    except Exception:
        return False
