# Streamlit Cloud 部署配置指南

本文档说明如何在 Streamlit Cloud 上配置应用以连接到 Supabase 数据库。

## 前置条件

1. ✅ 已创建 Supabase 项目
2. ✅ 已创建数据库表（见 DATABASE_SETUP.md）
3. ✅ 代码已推送到 GitHub
4. ✅ 记录了以下 Supabase 凭证：
   - **Project URL**: `https://detgroowhlgoqhwhilgk.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

## 步骤 1：在 Streamlit Cloud 部署应用

### 1.1 创建新应用

1. 访问 [Streamlit Cloud](https://share.streamlit.io/)
2. 点击 **New app**
3. 选择 GitHub 仓库：`wsewsewse0829/finance_modelling`
4. 选择分支：`main`
5. 设置文件路径：`finance_modelling/app.py`
6. 点击 **Deploy**

### 1.2 等待部署

Streamlit Cloud 会自动：
- 克隆代码
- 安装依赖（requirements.txt）
- 启动应用

部署通常需要 2-5 分钟。

## 步骤 2：配置 Streamlit Secrets

### 2.1 访问 Secrets 配置

1. 进入应用详情页
2. 点击左侧菜单 **Settings**
3. 点击 **Secrets**
4. 点击 **New secret**

### 2.2 添加 Supabase 凭证

添加以下两个 secrets：

#### Secret 1: SUPABASE_URL

```
https://detgroowhlgoqhwhilgk.supabase.co
```

- **Name**: `SUPABASE_URL`
- **Value**: 您的 Supabase 项目 URL
- **Description**: Supabase 项目 URL

点击 **Add** 保存。

#### Secret 2: SUPABASE_KEY

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRldGdyb293aGxnb3Fod2hpbGdrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI1MzYzMTUsImV4cCI6MjA4ODExMjMxNX0.UEcdjRPuVy7HZ7TH4rVszmCbgdNrjjSbtD35PuOIxUw
```

- **Name**: `SUPABASE_KEY`
- **Value**: 您的 Supabase anon public key
- **Description**: Supabase anon public key

点击 **Add** 保存。

### 2.3 验证 Secrets

配置完成后，Secrets 页面应该显示：

| Name | Value | Description |
|------|-------|-------------|
| SUPABASE_URL | `https://detgroow...` | Supabase 项目 URL |
| SUPABASE_KEY | `eyJhbGc...` | Supabase anon public key |

⚠️ **重要提示**：
- ✅ 只使用 **anon public key**，不要使用 service_role key
- ⚠️ service_role key 有完全权限，暴露会导致严重安全问题
- ✅ anon key 可以安全地暴露，因为受 RLS 保护

## 步骤 3：重新部署应用

添加 Secrets 后，需要重新部署应用才能生效：

1. 点击 **Settings** → **Overview**
2. 点击 **Restart**
3. 等待应用重新启动（约 1-2 分钟）

## 步骤 4：测试部署

### 4.1 访问应用

部署成功后，点击应用 URL 访问。

### 4.2 测试注册功能

1. 应用会显示登录页面
2. 切换到「注册」标签页
3. 输入邮箱和密码
4. 点击「注册」
5. 检查邮箱，点击验证链接
6. 切换回「登录」标签页，使用注册的账号登录

### 4.3 验证数据持久化

1. 登录后，上传一些数据（如科目表或序时账）
2. 刷新页面或重新登录
3. 确认数据仍然存在（不会丢失）

### 4.4 验证数据隔离

1. 使用浏览器无痕模式
2. 注册一个新用户
3. 上传不同的数据
4. 确认两个用户的数据完全独立

## 本地开发环境配置

### 创建 .env 文件

在项目根目录创建 `.env` 文件：

```bash
cd finance_modelling
touch .env
```

### 编辑 .env 文件

添加以下内容：

```env
SUPABASE_URL=https://detgroowhlgoqhwhilgk.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRldGdyb293aGxnb3Fod2hpbGdrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI1MzYzMTUsImV4cCI6MjA4ODExMjMxNX0.UEcdjRPuVy7HZ7TH4rVszmCbgdNrjjSbtD35PuOIxUw
```

### 加载 .env 文件

在 `app.py` 开头添加：

```python
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
```

### 运行本地应用

```bash
cd finance_modelling
streamlit run app.py
```

## 故障排查

### 问题 1：部署失败

**错误信息**：`ModuleNotFoundError: No module named 'supabase'`

**解决方案**：
1. 检查 `requirements.txt` 是否包含 `supabase==2.7.0`
2. 确认已推送到 GitHub
3. 在 Streamlit Cloud 手动触发重新部署

### 问题 2：连接数据库失败

**错误信息**：`Invalid API key` 或 `Connection refused`

**解决方案**：
1. 检查 Secrets 是否正确配置
2. 确认使用的是 anon public key
3. 验证 Supabase 项目 URL 是否正确

### 问题 3：登录失败

**错误信息**：`User not found` 或 `Invalid credentials`

**解决方案**：
1. 确认已验证邮箱
2. 检查邮箱和密码是否正确
3. 如果是新用户，先注册账号

### 问题 4：数据不持久化

**现象**：刷新页面后数据消失

**解决方案**：
1. 确认数据库表已创建（见 DATABASE_SETUP.md）
2. 检查 RLS 策略是否启用
3. 查看 Streamlit Cloud 日志是否有错误

### 问题 5：RLS 策略阻止访问

**错误信息**：`Permission denied for table accounts`

**解决方案**：
1. 在 Supabase Dashboard 检查 RLS 策略
2. 确认策略名称和逻辑正确
3. 查看用户是否已认证

## 监控和日志

### 查看应用日志

1. 进入应用详情页
2. 点击 **Logs**
3. 查看实时日志和错误信息

### 查看 Supabase 日志

1. 进入 Supabase Dashboard
2. 点击 **Logs**
3. 查看 API 请求和错误

## 安全最佳实践

### 1. 密钥管理

- ✅ 只在 Streamlit Cloud Secrets 中存储 anon public key
- ❌ 不要将 service_role key 提交到 Git
- ❌ 不要在代码中硬编码任何密钥

### 2. 用户数据保护

- ✅ RLS 自动隔离用户数据
- ✅ 每个用户只能访问自己的数据
- ✅ 删除用户时自动删除相关数据（ON DELETE CASCADE）

### 3. 定期备份

Supabase 自动备份数据，但建议：
- 定期导出重要数据
- 监控数据库使用量
- 设置告警通知

## 性能优化

### 1. 数据库索引

SQL 脚本已包含索引，确保已执行：
```sql
CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_general_ledger_user_id ON general_ledger(user_id);
-- 等等...
```

### 2. 批量操作

`saveGeneralLedger` 函数已实现批量插入（每批 1000 条）：
```python
batch_size = 1000
for i in range(0, len(data), batch_size):
    batch = data[i:i + batch_size]
    supabase.table('general_ledger').insert(batch).execute()
```

### 3. 缓存策略

Streamlit 自动缓存 session，可以利用：
```python
@st.cache_data
def loadAccountsCached():
    return loadAccounts()
```

## 成本估算

### Streamlit Cloud（免费版）

- ✅ 完全免费
- ✅ 750 小时/月
- ✅ 足够个人使用

### Supabase（免费版）

- ✅ 500MB 数据库存储
- ✅ 1GB 文件存储
- ✅ 2GB 带宽/月
- ✅ 50,000 API 请求/月

对于个人财务建模，免费版完全够用！

## 更新和维护

### 更新依赖

```bash
cd finance_modelling
pip install --upgrade -r requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### 更新数据库

如果需要修改数据库表结构：

1. 创建新的 SQL 迁移脚本
2. 在 Supabase SQL Editor 中执行
3. 更新代码以适应新结构
4. 推送代码并重新部署

## 参考资源

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-cloud)
- [Streamlit Secrets](https://docs.streamlit.io/streamlit-cloud/deploy-your-app/secrets-management)
- [Supabase Python Client](https://supabase.com/docs/reference/python)
- [Supabase Dashboard](https://supabase.com/dashboard)

## 支持

如果遇到问题：

1. 查看本文档的「故障排查」部分
2. 查看 Streamlit Cloud 和 Supabase 日志
3. 搜索相关文档和社区资源
4. 在 GitHub Issues 中提问

---

**恭喜！您已成功配置 Streamlit Cloud 应用连接到 Supabase 数据库！** 🎉