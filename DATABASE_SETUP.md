# 数据库设置指南

本文档说明如何在 Supabase 中创建必要的数据库表。

## 前置条件

1. 已创建 Supabase 项目
2. 记录了以下信息：
   - **Project URL**: `https://detgroowhlgoqhwhilgk.supabase.co`
   - **anon public key**: 已获取
   - **service_role key**: 已获取（保密）

## 步骤 1：创建数据库表

### 方法 A：使用 Supabase SQL Editor（推荐）

1. 访问 Supabase Dashboard
2. 进入项目 → **SQL Editor**
3. 点击 **New query**
4. 复制以下 SQL 代码并粘贴到编辑器
5. 点击 **Run** 执行

### 方法 B：使用命令行

```bash
psql -h db.detgroowhlgoqhwhilgk.supabase.co -p 5432 -d postgres -U postgres
```

然后粘贴以下 SQL 代码。

## SQL 脚本

```sql
-- ============================================
-- 财务建模应用 - 数据库表创建脚本
-- ============================================

-- 1. 科目表 (accounts)
-- 存储会计科目信息，每个用户有独立的科目表
CREATE TABLE IF NOT EXISTS accounts (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    account_code VARCHAR(20) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL,
    parent_code VARCHAR(20),
    balance_direction VARCHAR(10) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 确保同一用户下科目编码唯一
    UNIQUE(user_id, account_code)
);

-- 2. 序时账表 (general_ledger)
-- 存储所有会计分录，支持实际数据和预算数据
CREATE TABLE IF NOT EXISTS general_ledger (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    entry_date DATE NOT NULL,
    voucher_no VARCHAR(50),
    account_code VARCHAR(20) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    summary TEXT,
    actual_budget VARCHAR(10) DEFAULT '实际',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 工作底稿表 (working_papers)
-- 存储工作底稿文件的元数据
CREATE TABLE IF NOT EXISTS working_papers (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    upload_date DATE NOT NULL,
    file_size BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 创建索引以提高查询性能
-- ============================================

-- 科目表索引
CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_accounts_code ON accounts(account_code);

-- 序时账表索引
CREATE INDEX IF NOT EXISTS idx_general_ledger_user_id ON general_ledger(user_id);
CREATE INDEX IF NOT EXISTS idx_general_ledger_entry_date ON general_ledger(entry_date);
CREATE INDEX IF NOT EXISTS idx_general_ledger_account_code ON general_ledger(account_code);
CREATE INDEX IF NOT EXISTS idx_general_ledger_actual_budget ON general_ledger(actual_budget);

-- 工作底稿表索引
CREATE INDEX IF NOT EXISTS idx_working_papers_user_id ON working_papers(user_id);
CREATE INDEX IF NOT EXISTS idx_working_papers_filename ON working_papers(filename);

-- ============================================
-- 启用行级安全性 (RLS)
-- ============================================

-- 为所有表启用 RLS
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE general_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE working_papers ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 创建 RLS 策略
-- ============================================

-- 科目表策略
-- 用户只能查看、插入、更新、删除自己的科目
CREATE POLICY "Users can view own accounts" 
ON accounts FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own accounts" 
ON accounts FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own accounts" 
ON accounts FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own accounts" 
ON accounts FOR DELETE 
USING (auth.uid() = user_id);

-- 序时账表策略
-- 用户只能查看、插入、更新、删除自己的序时账
CREATE POLICY "Users can view own ledger" 
ON general_ledger FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own ledger" 
ON general_ledger FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own ledger" 
ON general_ledger FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own ledger" 
ON general_ledger FOR DELETE 
USING (auth.uid() = user_id);

-- 工作底稿表策略
-- 用户只能查看、插入、删除自己的工作底稿
CREATE POLICY "Users can view own working papers" 
ON working_papers FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own working papers" 
ON working_papers FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own working papers" 
ON working_papers FOR DELETE 
USING (auth.uid() = user_id);

-- ============================================
-- 更新时间戳触发器（可选）
-- ============================================

-- 创建更新时间戳的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为 accounts 表添加更新时间戳触发器
DROP TRIGGER IF EXISTS update_accounts_updated_at ON accounts;
CREATE TRIGGER update_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 验证表创建成功
-- ============================================

-- 检查表是否创建成功
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name IN ('accounts', 'general_ledger', 'working_papers')
ORDER BY table_name, ordinal_position;

-- 检查 RLS 是否启用
SELECT 
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('accounts', 'general_ledger', 'working_papers');

-- 检查策略是否创建成功
SELECT 
    schemaname,
    tablename,
    policyname
FROM pg_policies
WHERE schemaname = 'public'
    AND tablename IN ('accounts', 'general_ledger', 'working_papers')
ORDER BY tablename, policyname;
```

## 验证安装

执行 SQL 脚本后，检查以下内容：

### 1. 表是否创建成功

在 Supabase Dashboard → **Database** → **Tables** 中应该看到：
- ✅ `accounts`
- ✅ `general_ledger`
- ✅ `working_papers`

### 2. RLS 是否启用

在 Supabase Dashboard → **Database** → **Tables** → 选择表 → **Authentication** 中：
- ✅ **Enable RLS** 应该被勾选

### 3. 策略是否创建成功

在 Supabase Dashboard → **Database** → **Tables** → 选择表 → **Policies** 中应该看到：
- ✅ Users can view own [table]
- ✅ Users can insert own [table]
- ✅ Users can update own [table]
- ✅ Users can delete own [table]

## 数据模型说明

### accounts 表
| 列名 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| user_id | UUID | 用户 ID（外键） |
| account_code | VARCHAR(20) | 科目编码 |
| account_name | VARCHAR(100) | 科目名称 |
| account_type | VARCHAR(20) | 科目类型（资产/负债/所有者权益/收入/费用） |
| parent_code | VARCHAR(20) | 父科目编码 |
| balance_direction | VARCHAR(10) | 余额方向（借/贷） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

### general_ledger 表
| 列名 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| user_id | UUID | 用户 ID（外键） |
| entry_date | DATE | 凭证日期 |
| voucher_no | VARCHAR(50) | 凭证号 |
| account_code | VARCHAR(20) | 科目编码 |
| account_name | VARCHAR(100) | 科目名称 |
| debit_amount | DECIMAL(15,2) | 借方金额 |
| credit_amount | DECIMAL(15,2) | 贷方金额 |
| summary | TEXT | 摘要 |
| actual_budget | VARCHAR(10) | 实际/预算 |
| created_at | TIMESTAMPTZ | 创建时间 |

### working_papers 表
| 列名 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| user_id | UUID | 用户 ID（外键） |
| filename | VARCHAR(255) | 文件名 |
| upload_date | DATE | 上传日期 |
| file_size | BIGINT | 文件大小（字节） |
| created_at | TIMESTAMPTZ | 创建时间 |

## 安全性说明

### 行级安全性 (RLS)

所有表都启用了 RLS，确保：

1. **数据隔离**：每个用户只能访问自己的数据
2. **自动过滤**：查询时自动按 `user_id` 过滤
3. **防止越权**：即使知道其他用户的 ID 也无法访问

### 密钥管理

- ✅ **anon public key**：用于客户端（Streamlit）
- ⚠️ **service_role key**：仅用于管理员操作，保密！

## 故障排查

### 问题 1：表创建失败

**错误信息**：`relation already exists`

**解决方案**：表已存在，可以跳过或先删除：
```sql
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS general_ledger CASCADE;
DROP TABLE IF EXISTS working_papers CASCADE;
```

### 问题 2：RLS 策略创建失败

**错误信息**：`policy already exists`

**解决方案**：策略已存在，可以跳过或先删除：
```sql
DROP POLICY IF EXISTS "Users can view own accounts" ON accounts;
-- 对其他策略重复此操作
```

### 问题 3：外键约束错误

**错误信息**：`foreign key violation`

**解决方案**：确保先在 auth.users 中创建用户，再插入数据

## 下一步

数据库表创建完成后：

1. ✅ 配置 Streamlit Cloud Secrets（见 STREAMLIT_CLOUD_SETUP.md）
2. ✅ 测试注册和登录功能
3. ✅ 验证数据隔离（注册多个用户，确保数据不互通）

## 参考资料

- [Supabase Documentation](https://supabase.com/docs)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)