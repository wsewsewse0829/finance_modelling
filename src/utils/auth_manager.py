"""
认证管理模块
处理用户登录、注册、登出等认证相关功能
"""

import os
import requests
import streamlit as st
from typing import Optional, Dict, Any

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


def _make_auth_request(method: str, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """发送认证请求到 Supabase API"""
    url, key = _get_supabase_credentials()
    
    if not url or not key:
        raise Exception("Supabase 凭证未配置")
    
    auth_url = f"{url}{endpoint}"
    
    # 默认请求头
    default_headers = {
        "apikey": key,
        "Content-Type": "application/json"
    }
    
    # 合并自定义请求头
    if headers:
        default_headers.update(headers)
    
    try:
        if method == "GET":
            response = requests.get(auth_url, headers=default_headers)
        elif method == "POST":
            response = requests.post(auth_url, headers=default_headers, json=data)
        elif method == "DELETE":
            response = requests.delete(auth_url, headers=default_headers)
        else:
            raise Exception(f"不支持的 HTTP 方法: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = ""
        if hasattr(e.response, 'json'):
            try:
                error_json = e.response.json()
                error_detail = error_json.get('message', str(e))
            except:
                error_detail = str(e)
        else:
            error_detail = str(e)
        raise Exception(error_detail)


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
    
    try:
        st.write("调试: 尝试登录（使用 REST API）...")
        
        # 使用 Supabase REST API 进行登录
        # 尝试使用 /auth/v1/token 端点，在 body 中包含 grant_type
        response = _make_auth_request(
            method="POST",
            endpoint="/auth/v1/token",
            data={
                "grant_type": "password",
                "email": email,
                "password": password
            }
        )
        
        st.write(f"调试: 登录响应: {response}")
        
        # 检查响应
        if "access_token" in response and "user" in response:
            # 保存用户信息到 session
            st.session_state.user_id = str(response["user"]["id"])
            st.session_state.user_email = response["user"]["email"]
            st.session_state.access_token = response["access_token"]
            
            st.success(f"欢迎回来，{response['user']['email']}！")
            return True
        else:
            st.error("登录失败：响应格式错误")
            return False
    except requests.exceptions.HTTPError as e:
        # 显示详细的错误信息
        st.error(f"登录失败: HTTP {e.response.status_code} 错误")
        try:
            error_json = e.response.json()
            st.write(f"调试: 错误详情: {error_json}")
            error_msg = error_json.get('message', error_json.get('error_description', str(e)))
            st.error(f"详细错误: {error_msg}")
        except:
            st.write(f"调试: 响应内容: {e.response.text}")
            st.error(f"详细错误: {e.response.text}")
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
        st.write("调试: 尝试注册（使用 REST API）...")
        
        # 使用 Supabase REST API 进行注册
        # 根据 Supabase 文档，注册端点接受简单的 email 和 password
        response = _make_auth_request(
            method="POST",
            endpoint="/auth/v1/signup",
            data={
                "email": email,
                "password": password
            }
        )
        
        st.write(f"调试: 注册响应: {response}")
        
        # 检查响应
        # 注册成功后，Supabase 可能不返回 access_token（需要邮件确认）
        # 但我们已经禁用了邮件验证，所以应该返回 token
        if "access_token" in response and "user" in response:
            st.success("🎉 注册成功！")
            st.info("✅ 您的账户已创建，可以直接登录使用系统。")
            return True
        elif "user" in response:
            st.success("🎉 注册成功！")
            st.info("✅ 您的账户已创建，可以直接登录使用系统。")
            return True
        else:
            st.error("注册失败：响应格式错误")
            return False
    except requests.exceptions.HTTPError as e:
        error_msg = str(e)
        # 尝试从响应中获取详细错误信息
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_json = e.response.json()
                error_msg = error_json.get('message', error_msg)
                st.error(f"注册失败: {error_msg}")
            except:
                st.error(f"注册失败: {error_msg}")
        else:
            st.error(f"注册失败: {error_msg}")
        return False
    except Exception as e:
        error_msg = str(e)
        if "User already registered" in error_msg or "duplicate" in error_msg.lower():
            st.error("注册失败：该邮箱已被注册")
        elif "Password should be at least 6 characters" in error_msg or "password" in error_msg.lower():
            st.error("注册失败：密码至少需要 6 个字符")
        elif "Unable to validate email address" in error_msg or "email" in error_msg.lower():
            st.error("注册失败：邮箱格式不正确")
        else:
            st.error(f"注册失败: {error_msg}")
        return False


def logout() -> None:
    """用户登出"""
    try:
        # 使用 Supabase REST API 进行登出
        if 'access_token' in st.session_state:
            headers = {
                "Authorization": f"Bearer {st.session_state.access_token}"
            }
            _make_auth_request(
                method="POST",
                endpoint="/auth/v1/logout",
                headers=headers
            )
        
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
        if 'access_token' not in st.session_state:
            return False
        
        headers = {
            "Authorization": f"Bearer {st.session_state.access_token}"
        }
        
        # 使用 Supabase REST API 获取当前用户
        response = _make_auth_request(
            method="GET",
            endpoint="/auth/v1/user",
            headers=headers
        )
        
        if response and "id" in response:
            return True
        return False
    except Exception:
        return False


def diagnose_supabase() -> Dict[str, Any]:
    """诊断 Supabase 配置和连接
    
    Returns:
        Dict[str, Any]: 诊断结果
    """
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
        
        # 3. 检查认证端点
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
        
        # 4. 检查注册端点（发送一个无效的请求）
        try:
            response = requests.post(
                f"{url}/auth/v1/signup",
                headers={
                    "apikey": key,
                    "Content-Type": "application/json"
                },
                json={},  # 空的请求体会返回 400，但说明端点可访问
                timeout=10
            )
            results["signup_endpoint_accessible"] = response.status_code in [400, 422]
        except Exception as e:
            results["errors"].append(f"无法访问注册端点: {str(e)}")
        
        # 5. 检查登录端点（发送一个无效的请求）
        try:
            response = requests.post(
                f"{url}/auth/v1/token",
                headers={
                    "apikey": key,
                    "Content-Type": "application/json"
                },
                json={},  # 空的请求体会返回 400，但说明端点可访问
                timeout=10
            )
            results["login_endpoint_accessible"] = response.status_code in [400, 422]
        except Exception as e:
            results["errors"].append(f"无法访问登录端点: {str(e)}")
        
        # 6. 尝试获取项目信息（检查 Key 是否有效）
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
