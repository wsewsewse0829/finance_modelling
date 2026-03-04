"""
数据管理工具
使用 Supabase 数据库管理所有数据的持久化存储
支持用户数据隔离，每个用户只能访问自己的数据
"""

import os
import pandas as pd
from typing import Optional
from supabase import create_client, Client

def _get_supabase_client() -> Client:
    """获取 Supabase 客户端（使用用户认证 token）"""
    import streamlit as st
    
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
            pass
    
    if not url or not key:
        raise Exception("Supabase 凭证未配置")
    
    # 创建客户端
    client = create_client(url, key)
    
    # 如果用户已登录，设置认证 token
    if 'access_token' in st.session_state and st.session_state.access_token:
        client.auth.set_session(st.session_state.access_token)
    
    return client

# 保留文件目录用于工作底稿文件存储
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
WORKING_PAPERS_DIR = os.path.join(DATA_DIR, "working_papers")


def ensureDataDir() -> None:
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)


def _get_user_id() -> str:
    """获取当前用户 ID
    
    Returns:
        str: 用户 ID
        
    Raises:
        Exception: 用户未登录时抛出异常
    """
    import streamlit as st
    
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        raise Exception("用户未登录，无法访问数据")
    
    return st.session_state.user_id


def loadAccounts() -> pd.DataFrame:
    """加载当前用户的科目表数据
    
    Returns:
        pd.DataFrame: 科目表数据
        
    Raises:
        Exception: 用户未登录或数据库查询失败
    """
    try:
        user_id = _get_user_id()
        client = _get_supabase_client()
        
        # 从 Supabase 查询用户的科目表
        response = client.table('accounts').select('*').eq('user_id', user_id).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # 移除 Supabase 自动添加的字段（id, user_id, created_at, updated_at）
            columns_to_drop = ['id', 'user_id', 'created_at', 'updated_at']
            df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
            return df
        else:
            # 如果没有数据，创建默认科目表
            return _createDefaultAccounts()
    except Exception as e:
        raise Exception(f"加载科目表失败: {str(e)}")


def saveAccounts(df: pd.DataFrame) -> None:
    """保存当前用户的科目表数据
    
    Args:
        df: 科目表数据
        
    Raises:
        Exception: 用户未登录或数据库操作失败
    """
    try:
        user_id = _get_user_id()
        client = _get_supabase_client()
        
        # 删除用户的所有旧科目数据
        client.table('accounts').delete().eq('user_id', user_id).execute()
        
        # 准备新数据
        data = df.to_dict('records')
        for record in data:
            record['user_id'] = user_id
        
        # 批量插入新数据（如果数据量大，可以考虑分批插入）
        if data:
            client.table('accounts').insert(data).execute()
            
    except Exception as e:
        raise Exception(f"保存科目表失败: {str(e)}")


def loadGeneralLedger() -> pd.DataFrame:
    """加载当前用户的序时账数据
    
    Returns:
        pd.DataFrame: 序时账数据
        
    Raises:
        Exception: 用户未登录或数据库查询失败
    """
    try:
        user_id = _get_user_id()
        client = _get_supabase_client()
        
        # 从 Supabase 查询用户的序时账
        response = client.table('general_ledger').select('*').eq('user_id', user_id).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # 移除 Supabase 自动添加的字段
            columns_to_drop = ['id', 'user_id', 'created_at']
            df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
            
            # 转换日期为统一的字符串格式 YYYY-MM-DD，避免时区问题
            if 'entry_date' in df.columns:
                df["entry_date"] = pd.to_datetime(df["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
                # 过滤掉日期转换失败的记录
                df = df[df["entry_date"].notna()]
            
            # 确保数值列的正确类型
            if 'debit_amount' in df.columns:
                df["debit_amount"] = pd.to_numeric(df["debit_amount"], errors="coerce").fillna(0)
            if 'credit_amount' in df.columns:
                df["credit_amount"] = pd.to_numeric(df["credit_amount"], errors="coerce").fillna(0)
            
            # 如果actual/budget列不存在，添加默认值"实际"
            if "actual_budget" not in df.columns:
                df["actual_budget"] = "实际"
            
            return df
        else:
            # 返回空数据框
            return pd.DataFrame(columns=[
                "entry_date", "voucher_no", "account_code",
                "account_name", "debit_amount", "credit_amount", "summary", "actual_budget"
            ])
    except Exception as e:
        raise Exception(f"加载序时账失败: {str(e)}")


def saveGeneralLedger(df: pd.DataFrame) -> None:
    """保存当前用户的序时账数据
    
    Args:
        df: 序时账数据
        
    Raises:
        Exception: 用户未登录或数据库操作失败
    """
    try:
        user_id = _get_user_id()
        client = _get_supabase_client()
        
        # 删除用户的所有旧序时账数据
        client.table('general_ledger').delete().eq('user_id', user_id).execute()
        
        # 准备新数据
        data = df.to_dict('records')
        for record in data:
            record['user_id'] = user_id
        
        # 批量插入新数据（如果数据量大，可以考虑分批插入）
        if data:
            # Supabase 的 batch insert 限制为每次 1000 条记录
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                client.table('general_ledger').insert(batch).execute()
            
    except Exception as e:
        raise Exception(f"保存序时账失败: {str(e)}")



def getWorkingPapersList() -> pd.DataFrame:
    """获取当前用户的工作底稿列表
    
    Returns:
        pd.DataFrame: 工作底稿列表
        
    Raises:
        Exception: 用户未登录或数据库查询失败
    """
    try:
        user_id = _get_user_id()
        client = _get_supabase_client()
        
        # 从 Supabase 查询用户的工作底稿
        response = client.table('working_papers').select('*').eq('user_id', user_id).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # 移除 Supabase 自动添加的字段
            columns_to_drop = ['id', 'user_id', 'created_at']
            df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
            return df
        else:
            # 返回空数据框
            return pd.DataFrame(columns=["filename", "upload_date", "file_size"])
    except Exception as e:
        raise Exception(f"加载工作底稿列表失败: {str(e)}")


def saveWorkingPaper(filename: str, upload_date: str, file_size: int) -> None:
    """保存当前用户的工作底稿元数据
    
    Args:
        filename: 文件名
        upload_date: 上传日期
        file_size: 文件大小（字节）
        
    Raises:
        Exception: 用户未登录或数据库操作失败
    """
    try:
        user_id = _get_user_id()
        client = _get_supabase_client()
        
        # 插入新记录
        data = {
            "user_id": user_id,
            "filename": filename,
            "upload_date": upload_date,
            "file_size": file_size
        }
        
        client.table('working_papers').insert(data).execute()
            
    except Exception as e:
        raise Exception(f"保存工作底稿元数据失败: {str(e)}")


def deleteWorkingPaper(filename: str) -> bool:
    """删除工作底稿
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否删除成功
        
    Raises:
        Exception: 用户未登录或数据库操作失败
    """
    try:
        user_id = _get_user_id()
        client = _get_supabase_client()
        
        # 删除文件
        file_path = os.path.join(WORKING_PAPERS_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 从 Supabase 删除元数据
        response = client.table('working_papers').delete().eq('user_id', user_id).eq('filename', filename).execute()
        
        return True
    except Exception as e:
        raise Exception(f"删除工作底稿失败: {str(e)}")


def getWorkingPaperPath(filename: str) -> str:
    """获取工作底稿文件路径"""
    ensureDataDir()
    os.makedirs(WORKING_PAPERS_DIR, exist_ok=True)
    return os.path.join(WORKING_PAPERS_DIR, filename)


def saveTrialBalance(df: pd.DataFrame) -> None:
    """保存当前用户的科目余额表数据
    
    Args:
        df: 科目余额表数据
        
    Raises:
        Exception: 用户未登录或数据库操作失败
    """
    try:
        user_id = _get_user_id()
        client = _get_supabase_client()
        
        # 删除用户的所有旧科目余额表数据
        client.table('trial_balance').delete().eq('user_id', user_id).execute()
        
        # 准备新数据
        data = df.to_dict('records')
        for record in data:
            record['user_id'] = user_id
        
        # 批量插入新数据
        if data:
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                client.table('trial_balance').insert(batch).execute()
            
    except Exception as e:
        raise Exception(f"保存科目余额表失败: {str(e)}")


def saveReport(df: pd.DataFrame) -> None:
    """保存当前用户的会计报表数据
    
    Args:
        df: 会计报表数据
        
    Raises:
        Exception: 用户未登录或数据库操作失败
    """
    try:
        user_id = _get_user_id()
        client = _get_supabase_client()
        
        # 删除用户的所有旧会计报表数据
        client.table('reports').delete().eq('user_id', user_id).execute()
        
        # 准备新数据
        data = df.to_dict('records')
        for record in data:
            record['user_id'] = user_id
        
        # 批量插入新数据
        if data:
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                client.table('reports').insert(batch).execute()
            
    except Exception as e:
        raise Exception(f"保存会计报表失败: {str(e)}")


def _createDefaultAccounts() -> pd.DataFrame:
    """创建默认科目表"""
    default_accounts = [
        # 资产类
        {"account_code": "1001", "account_name": "现金", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        {"account_code": "1002", "account_name": "银行存款", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        {"account_code": "1101", "account_name": "短期投资", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        {"account_code": "1201", "account_name": "应收账款", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        {"account_code": "1501", "account_name": "固定资产", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        {"account_code": "1601", "account_name": "长期投资", "account_type": "资产", "parent_code": "", "balance_direction": "借"},
        # 负债类
        {"account_code": "2001", "account_name": "短期借款", "account_type": "负债", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "2201", "account_name": "应付账款", "account_type": "负债", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "2501", "account_name": "长期借款", "account_type": "负债", "parent_code": "", "balance_direction": "贷"},
        # 所有者权益类
        {"account_code": "3001", "account_name": "实收资本", "account_type": "所有者权益", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "3101", "account_name": "资本公积", "account_type": "所有者权益", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "3201", "account_name": "留存收益", "account_type": "所有者权益", "parent_code": "", "balance_direction": "贷"},
        # 收入类
        {"account_code": "4001", "account_name": "工资收入", "account_type": "收入", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "4101", "account_name": "投资收益", "account_type": "收入", "parent_code": "", "balance_direction": "贷"},
        {"account_code": "4201", "account_name": "其他收入", "account_type": "收入", "parent_code": "", "balance_direction": "贷"},
        # 费用类
        {"account_code": "5001", "account_name": "生活费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
        {"account_code": "5101", "account_name": "交通费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
        {"account_code": "5201", "account_name": "娱乐费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
        {"account_code": "5301", "account_name": "教育费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
        {"account_code": "5401", "account_name": "医疗费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
        {"account_code": "5501", "account_name": "其他费用", "account_type": "费用", "parent_code": "", "balance_direction": "借"},
    ]
    df = pd.DataFrame(default_accounts)
    saveAccounts(df)
    return df
