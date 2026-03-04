"""
首页
展示应用介绍和主要功能概览
"""

import streamlit as st


def renderHomePage() -> None:
    """渲染首页"""
    st.title("💰 个人财务规划应用")
    st.markdown("---")

    # 欢迎卡片
    with st.container():
        st.markdown("""
        <div class="stCard">
            <h2>欢迎使用个人财务规划应用！</h2>
            <p>本应用采用 <strong>企业财务管理的思维</strong> 来管理个人财务，帮助您做好个人的财务规划。
            同时也可以用于上市公司财报的简单分析。</p>
            <div style="margin-top: 16px; padding: 12px; background-color: #E3F2FD; border-left: 4px solid #2196F3; border-radius: 4px;">
                <strong>🆕 最新功能：预实分析</strong><br>
                • 对比实际数据与预算数据<br>
                • 多期间数据自动汇总<br>
                • 清晰的差异分析报表<br>
                • 可视化图表展示
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 功能介绍卡片
    col1, col2 = st.columns(2)

    with col1:
        # 会计报表卡片
        st.markdown("""
        <div class="stCard">
            <h3>📊 会计报表</h3>
            <ul style="margin-left: 20px; color: #666666;">
                <li>资产负债表</li>
                <li>利润表</li>
                <li>多期间对比展示</li>
                <li>可视化图表分析</li>
                <li>默认显示全部期间</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # 预实分析卡片
        st.markdown("""
        <div class="stCard">
            <h3>📈 预实分析</h3>
            <ul style="margin-left: 20px; color: #666666;">
                <li>资产负债表预实对比</li>
                <li>利润表预实对比</li>
                <li>预实差异可视化分析</li>
                <li>多期间数据汇总</li>
                <li>实际|预算|预实差异三列展示</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # 科目管理卡片
        st.markdown("""
        <div class="stCard">
            <h3>📋 科目管理</h3>
            <ul style="margin-left: 20px; color: #666666;">
                <li>预设标准科目体系</li>
                <li>自定义次级科目</li>
                <li>科目类型管理</li>
                <li>科目编码体系</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # 数据上传卡片
        st.markdown("""
        <div class="stCard">
            <h3>📤 数据上传</h3>
            <ul style="margin-left: 20px; color: #666666;">
                <li>批量上传序时账</li>
                <li>支持 CSV/Excel 格式</li>
                <li>自动借贷平衡校验</li>
                <li>自动生成科目余额表</li>
                <li>支持实际/预算数据分类</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # 自动校验卡片
        st.markdown("""
        <div class="stCard">
            <h3>🔍 自动校验</h3>
            <ul style="margin-left: 20px; color: #666666;">
                <li>序时账借贷平衡校验</li>
                <li>会计报表平衡校验</li>
                <li>数据完整性检查</li>
                <li>错误提示与修正建议</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # 可视化图表卡片
        st.markdown("""
        <div class="stCard">
            <h3>📉 可视化图表</h3>
            <ul style="margin-left: 20px; color: #666666;">
                <li>资产/负债/权益结构分析</li>
                <li>收入/费用结构分析</li>
                <li>科目趋势分析</li>
                <li>预实差异分析图表</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 快速开始指南
    st.markdown("""
    ### 🚀 快速开始

    1. **科目管理** → 查看和自定义您的会计科目
    2. **数据上传** → 上传您的序时账数据（CSV格式，支持实际数据和预算数据）
    3. **会计报表** → 查看自动生成的财务报表和可视化图表
    4. **预实分析** → 对比实际与预算数据，分析差异
    """)

    st.markdown("""
    ### 💡 使用提示

    - **会计报表**：查看所有期间或指定期间的财务状况，默认显示全部期间
    - **预实分析**：上传预算数据后，可对比实际数据与预算数据的差异
    - **数据格式**：序时账需包含 `actual_budget` 列标注为"实际"或"预算"
    - **预实对比**：选择多个期间时，系统自动汇总各期间的实际金额和预算金额
    """)

    st.info("💡 系统已预设了一套适合个人财务管理的标准科目体系，您可以直接使用或根据需要自定义。")
