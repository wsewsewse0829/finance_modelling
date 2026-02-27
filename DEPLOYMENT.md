# 应用部署指南

本文档介绍如何在其他设备上访问和编辑Finance Modelling应用。

## 方案一：局域网访问（推荐）

如果在同一局域网内，其他设备可以通过网络URL访问。

### 步骤

1. **启动应用**
   ```bash
   cd /Users/wushengen/Finance_modelling/finance_modelling
   streamlit run app.py
   ```

2. **查看网络URL**
   启动后会显示：
   ```
   Network URL: http://172.20.10.2:8501
   External URL: http://39.144.156.120:8501
   ```

3. **其他设备访问**
   - 手机/平板：在浏览器中输入 `http://39.144.156.120:8501`
   - 同一WiFi下的电脑：输入 `http://172.20.10.2:8501`

**注意**：
- 主机电脑必须保持运行且不能休眠
- 防火墙需要允许8501端口访问

---

## 方案二：云平台部署（推荐用于远程访问）

### Streamlit Cloud（免费，最简单）

1. **准备代码**
   ```bash
   # 将代码推送到GitHub
   cd /Users/wushengen/Finance_modelling
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/你的用户名/finance-modelling.git
   git push -u origin main
   ```

2. **部署到Streamlit Cloud**
   - 访问：https://share.streamlit.io
   - 点击 "New app"
   - 连接GitHub仓库
   - 选择 `finance_modelling` 文件夹
   - 主文件路径：`app.py`
   - 点击 "Deploy"

3. **访问应用**
   部署完成后，你会获得一个永久URL，如：`https://你的应用名.streamlit.app`

**注意**：Streamlit Cloud需要文件结构在根目录，如果遇到问题，可以创建符号链接或调整文件结构。

---

## 方案三：本地服务器 + 内网穿透

使用ngrok等工具将本地服务暴露到公网。

### 使用ngrok

1. **安装ngrok**
   ```bash
   brew install ngrok  # macOS
   ```

2. **启动Streamlit应用**
   ```bash
   cd /Users/wushengen/Finance_modelling/finance_modelling
   streamlit run app.py
   ```

3. **在新终端启动ngrok**
   ```bash
   ngrok http 8501
   ```

4. **复制公网URL**
   ngrok会显示一个临时URL，如：`https://abc123.ngrok-free.app`

5. **其他设备访问**
   使用ngrok提供的URL访问

**注意**：
- ngrok免费版URL会变化
- 需要保持ngrok进程运行

---

## 方案四：部署到VPS/云服务器

### 部署到阿里云/腾讯云/AWS等

1. **购买服务器**
   - 选择配置：1核2G内存即可
   - 安装系统：Ubuntu 20.04或更高版本

2. **服务器配置**
   ```bash
   # SSH连接服务器
   ssh root@服务器IP

   # 安装Python和pip
   apt update
   apt install python3 python3-pip

   # 安装依赖
   pip install streamlit pandas plotly

   # 上传代码（使用git或scp）
   git clone 你的GitHub仓库

   # 启动应用
   cd finance_modelling
   nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > app.log 2>&1 &
   ```

3. **配置防火墙**
   ```bash
   # 阿里云/腾讯云控制台开放8501端口
   ```

4. **访问应用**
   `http://服务器IP:8501`

---

## 数据共享

### 方案A：使用Git同步数据文件

将`data/`目录纳入版本控制，多人共享数据：

```bash
cd /Users/wushengen/Finance_modelling
git add data/*.csv
git commit -m "Update data"
git push
```

其他设备拉取最新数据：
```bash
git pull
```

### 方案B：使用云存储

将`data/`目录同步到：
- Google Drive
- Dropbox
- OneDrive
- 阿里云盘

然后在每个设备上将云盘挂载到`data/`目录。

### 方案C：使用数据库（生产环境推荐）

将CSV存储改为数据库（SQLite/MySQL/PostgreSQL）：

```python
# 示例：使用SQLite
import sqlite3

def getConnection():
    conn = sqlite3.connect('finance.db')
    return conn
```

---

## 安全建议

1. **添加认证**
   在`.streamlit/config.toml`中：
   ```toml
   [server]
   enableCORS = true
   ```

2. **使用HTTPS**
   - Streamlit Cloud自动提供HTTPS
   - 自建服务器需要配置SSL证书（使用Let's Encrypt）

3. **数据备份**
   ```bash
   # 定期备份数据
   tar -czf backup_$(date +%Y%m%d).tar.gz data/
   ```

---

## 推荐方案

| 场景 | 推荐方案 | 难度 | 成本 |
|--------|----------|--------|------|
| 家庭内网使用 | 局域网访问 | ⭐ | 免费 |
| 随时随地访问 | Streamlit Cloud | ⭐⭐ | 免费 |
| 团队协作 | VPS + 数据库 | ⭐⭐⭐ | $5-10/月 |

---

## 常见问题

### Q: 局域网访问失败？
A: 检查防火墙设置，确保8501端口开放。

### Q: Streamlit Cloud部署失败？
A: 确保根目录有`app.py`，文件结构正确。

### Q: 数据不同步？
A: 实现数据库方案，避免多设备同时编辑CSV。

### Q: 性能问题？
A: 使用云服务器或升级Streamlit Cloud套餐。

---

## 联系支持

如有问题，请查看：
- Streamlit官方文档：https://docs.streamlit.io
- 项目README.md
- 技术设计文档：TECH_DESIGN.md