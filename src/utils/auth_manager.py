"""
认证管理模块
处理用户登录、注册、登出等认证相关功能
使用官方 Supabase Python SDK
"""

import os
import streamlit as st
from supabase import create_client
from typing import Optional, Dict, Any

# 从环境变量或 Streamlit secrets 获取 Supabase 凭证
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


# 创建全局 Supabase 客户端（使用官方 SDK）
_supabase_client = None

def _get_supabase_client():
    """获取 Supabase 客户端（延迟初始化）"""
    global _supabase_client
    if _supabase_client is None:
        url, key = _get_supabase_credentials()
        
        st.write(f"调试: URL = {url[:20]}..." if url else "调试: URL = None")
        st.write(f"调试: Key = {key[:20]}..." if key else "调试: Key = None")
        
        if not url or not key:
            raise Exception("Supabase 凭证未配置")
        
        try:
            _supabase_client = create_client(url, key)
            
            # 验证客户端是否正确创建
            if _supabase_client is None:
                raise Exception("create_client 返回了 None")
            
            if _supabase_client.auth is None:
                raise Exception("client.auth 为 None，认证模块未正确初始化")
            
            st.write("调试: Supabase 客户端创建成功")
            
        except Exception as e:
            st.write(f"调试: 创建客户端失败: {str(e)}")
            raise Exception(f"创建 Supabase 客户端失败: {str(e)}")
    
    # 再次验证客户端和 auth
    if _supabase_client is None or _supabase_client.auth is None:
        raise Exception("Supabase 客户端或认证模块未正确初始化")
    
    return _supabase_client


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
    """用户登录（使用官方 SDK）
    
    Args:
        email: 用户邮箱
        password: 用户密码
        
    Returns:
        bool: 登录是否成功
    """
    try:
        st.write("调试: 尝试登录（使用官方 SDK）...")
        
        # 使用官方 SDK 进行登录
        client = _get_supabase_client()
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        st.write(f"调试: 登录响应: {response}")
        
        # 检查响应
        if response.user:
            # 保存用户信息到 session
            st.session_state.user_id = str(response.user.id)
            st.session_state.user_email = response.user.email
            st.session_state.access_token = response.session.access_token if response.session else None
            
            st.success(f"欢迎回来，{response.user.email}！")
            return True
        else:
            st.error("登录失败：用户信息异常")
            return False
            
    except Exception as e:
        error_msg = str(e)
        st.error(f"登录异常: {error_msg}")
        
        # 友好的错误提示
        if "Invalid login credentials" in error_msg or "invalid login credentials" in error_msg.lower():
            st.error("登录失败：邮箱或密码错误")
        elif "Email not confirmed" in error_msg:
            st.error("登录失败：请先验证邮箱")
        elif "No API key found" in error_msg or "No apikey" in error_msg:
            st.error("登录失败：Supabase API Key 配置错误")
        
        return False


def register(email: str, password: str) -> bool:
    """用户注册（使用官方 SDK）
    
    Args:
        email: 用户邮箱
        password: 用户密码
        
    Returns:
        bool: 注册是否成功
    """
    try:
        st.write("调试: 尝试注册（使用官方 SDK）...")
        
        # 使用官方 SDK 进行注册
        client = _get_supabase_client()
        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "email_confirm": True  # 自动确认邮箱，无需邮件验证
            }
        })
        
        st.write(f"调试: 注册响应: {response}")
        
        # 检查响应
        if response.user:
            st.success("🎉 注册成功！")
            st.info("✅ 您的账户已创建，可以直接登录使用系统。")
            return True
        else:
            st.error("注册失败：用户信息异常")
            return False
            
    except Exception as e:
        error_msg = str(e)
        st.error(f"注册异常: {error_msg}")
        
        # 友好的错误提示
        if "User already registered" in error_msg or "duplicate" in error_msg.lower():
            st.error("注册失败：该邮箱已被注册")
        elif "Password should be at least 6 characters" in error_msg or "password" in error_msg.lower():
            st.error("注册失败：密码至少需要 6 个字符")
        elif "Unable to validate email address" in error_msg or "email" in error_msg.lower():
            st.error("注册失败：邮箱格式不正确")
        elif "No API key found" in error_msg or "No apikey" in error_msg:
            st.error("注册失败：Supabase API Key 配置错误")
        
        return False


def logout() -> None:
    """用户登出（使用官方 SDK）"""
    try:
        # 使用官方 SDK 进行登出
        client = _get_supabase_client()
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
    """刷新用户 session（使用官方 SDK）
    
    Returns:
        bool: 刷新是否成功
    """
    try:
        if 'access_token' not in st.session_state:
            return False
        
        # 使用官方 SDK 获取当前用户
        client = _get_supabase_client()
        user = client.auth.get_user()
        
        if user:
            return True
        return False
    except Exception:
        return False


def diagnose_supabase() -> Dict[str, Any]:
    """诊断 Supabase 配置和连接
    
    Returns:
        Dict[str, Any]: 诊断结果
    """
    import requests
    
    results = {
        "url_configured": False,
        "key_configured": False,
        "url_accessible": False,
        "auth_endpoint_accessible": False,
        "signup_endpoint_accessible": False,
        "user_exists": False,
        "email_verification_enabled": None,
        "errors": []
    }
    
    try:
        # 1. 检查凭证是否配置
        url, key = _get_supabase_credentials()
        results["url_configured"] = bool(url)
        results["key_configured"] = bool(key)
        
        if not url or not key:
            results["errors"].append("Supabase URL 或 Key 未配置")
            return results
        
        # 2. 检查 URL 是否可访问
        try:
            response = requests.get(url, timeout=10)
            results["url_accessible"] = response.status_code == 200
        except Exception as e:
            results["errors"].append(f"无法访问 Supabase URL: {str(e)}")
        
        # 3. 尝试使用官方 SDK 创建客户端
        try:
            client = create_client(url, key)
            results["sdk_client_created"] = True
        except Exception as e:
            results["sdk_client_created"] = False
            results["errors"].append(f"无法创建 SDK 客户端: {str(e)}")
        
        # 4. 检查认证端点
        try:
            response = requests.get(
                f"{url}/auth/v1/user",
                headers={
                    "apikey": key,
                    "Authorization": f"Bearer {key}"
                },
                timeout=10
            )
            results["auth_endpoint_accessible"] = response.status_code in [200, 401]
        except Exception as e:
            results["errors"].append(f"无法访问认证端点: {str(e)}")
        
        # 5. 尝试获取项目信息（检查 Key 是否有效）
        try:
            response = requests.get(
                f"{url}/rest/v1/",
                headers={
                    "apikey": key,
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            results["api_key_valid"] = response.status_code == 200
            if response.status_code != 200:
                results["errors"].append(f"API Key 可能无效 (HTTP {response.status_code})")
        except Exception as e:
            results["api_key_valid"] = False
            results["errors"].append(f"API Key 验证失败: {str(e)}")
        
    except Exception as e:
        results["errors"].append(f"诊断过程出错: {str(e)}")
    
    return results