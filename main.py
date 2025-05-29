# 必须放在最开始的Streamlit命令
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import pyplot as plt
import seaborn as sns
import os
import pandas as pd
import openpyxl
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from utils import dataframe_agent


import warnings
from langchain_core._api.deprecation import LangChainDeprecationWarning

# 忽略弃用警告
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

# 然后继续使用旧代码
from langchain.memory import ConversationBufferMemory
st.session_state['memory'] = ConversationBufferMemory()


plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为SimHei
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题

st.set_page_config(
    page_title="互联数据分析智能体",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main .block-container {
        max-width: 95%;
        padding-top: 1rem;
    }
    .data-section {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .analysis-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #4a6baf;
    }
    .visualization-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #28a745;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4a6baf;
        color: white;
    }
    .chart-container {
        margin-top: 20px;
        padding: 15px;
        border: 1px solid #eaeaea;
        border-radius: 8px;
        background: white;
    }
    .data-insight {
        padding: 15px;
        background-color: #f0f8ff;
        border-radius: 8px;
        margin-top: 15px;
    }
    .axis-label {
        font-size: 14px;
        font-weight: bold;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'messages' not in st.session_state:
    st.session_state['messages'] = [{'role': 'ai', 'content': '你好主人，我是你的AI助手，我叫小美'}]
    st.session_state['memory'] = ConversationBufferMemory()
    st.session_state['API_KEY'] = ''
    st.session_state['df'] = None
    st.session_state['data_loaded'] = False

# 侧边栏内容
with st.sidebar:
    st.subheader("🔑 OpenAI API 设置")
    new_api_key = st.text_input('请输入OpenAI API Key:',
                                type='password',
                                value=st.session_state['API_KEY'],
                                help="请输入有效的OpenAI API密钥以启用AI功能")

    if st.button('验证API密钥', key='verify_api_key'):
        if new_api_key.strip() == '':
            st.error('API密钥不能为空！')
        else:
            st.session_state['API_KEY'] = new_api_key
            st.success('API密钥验证成功！')

    st.markdown("---")
    function_selector = st.radio(
        "选择功能模式:",
        ("数据分析", "AI聊天"),
        index=0,
        horizontal=True
    )

# 主内容区域
st.title("📈 智能数据分析平台")
st.markdown("---")

# ==================== 数据分析功能 ====================
if function_selector == "数据分析":
    # 数据上传部分

    upload_col, preview_col = st.columns([1, 1])

    with upload_col:
        with st.expander("📂 上传数据", expanded=True):
            file_type = st.radio("选择文件类型:", ["Excel", "CSV"], index=0, horizontal=True)
            uploaded_file = st.file_uploader(f"上传{file_type}文件",
                                             type="xlsx" if file_type == "Excel" else "csv",
                                             help="支持.xlsx和.csv格式，最大100MB")

            if uploaded_file:
                try:
                    if file_type == "Excel":
                        wb = openpyxl.load_workbook(uploaded_file)
                        sheet_names = wb.sheetnames
                        selected_sheet = st.selectbox("选择工作表:", sheet_names)
                        st.session_state['df'] = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
                    else:
                        st.session_state['df'] = pd.read_csv(uploaded_file)

                    st.session_state['data_loaded'] = True
                    st.success("数据加载成功!")

                except Exception as e:
                    st.error(f"数据加载失败: {str(e)}")
                    st.session_state['data_loaded'] = False

    # 数据预览部分
    if st.session_state.get('data_loaded', False):
        with preview_col:
            with st.expander("👀 数据预览", expanded=True):
                st.dataframe(st.session_state['df'].head(8), use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("总行数", st.session_state['df'].shape[0])
                with col2:
                    st.metric("总列数", st.session_state['df'].shape[1])

                st.markdown("**数据类型分布**")
                dtype_counts = st.session_state['df'].dtypes.value_counts()
                dtype_df = pd.DataFrame({
                    '数据类型': dtype_counts.index.astype(str),
                    '数量': dtype_counts.values
                })
                st.dataframe(dtype_df, hide_index=True)

    # 数据分析部分
    if st.session_state.get('data_loaded', False):
        # 分析和可视化标签页
        tab1, tab2 = st.tabs(["🔍 数据分析", "📊 数据可视化"])

        with tab1:
            st.markdown("### 智能数据分析")
            query = st.text_area("输入您的分析问题:",
                                 height=100,
                                 placeholder="例如: 显示销售额最高的5个产品\n或: 计算各地区的平均销售额")

            if st.button("执行分析", key="run_analysis"):
                if not query:
                    st.warning("请输入分析问题")
                else:
                    with st.spinner("AI正在分析数据..."):
                        try:
                            result = dataframe_agent(st.session_state["df"], query)

                            with st.container():
                                st.markdown("#### 分析结果")
                                if "answer" in result:
                                    st.markdown(result["answer"])
                                else:
                                    st.info("未生成分析结果")

                            if "table" in result:
                                with st.container():
                                    st.markdown("#### 数据表格")
                                    st.dataframe(pd.DataFrame(
                                        result["table"]["data"],
                                        columns=result["table"]["columns"]
                                    ), use_container_width=True)

                        except Exception as e:
                            error_msg = str(e)
                            if '402' in error_msg or 'Insufficient Balance' in error_msg:
                                st.error("分析失败: OpenAI API 余额不足，请充值或检查API密钥")
                            else:
                                st.error(f"分析失败: {error_msg}")

        with tab2:
            st.markdown("### 交互式数据可视化")
            if st.session_state['df'] is not None:
                # 获取数值列和非数值列
                numeric_cols = st.session_state['df'].select_dtypes(include=['number']).columns.tolist()
                other_cols = [col for col in st.session_state['df'].columns if col not in numeric_cols]

                # 确保有足够的列进行可视化
                if len(numeric_cols) == 0:
                    st.warning("数据中没有数值列，无法进行可视化分析")
                elif len(other_cols) == 0:
                    st.warning("数据中没有分类列，无法进行分组可视化")
                else:
                    # 图表类型选择
                    chart_options = ["柱状图", "折线图", "散点图", "饼图"]
                    chart_type = st.selectbox("选择图表类型", chart_options, index=0)

                    # 列选择器
                    col1, col2 = st.columns(2)

                    with col1:
                        # X轴选择（分类数据）
                        x_options = other_cols if other_cols else st.session_state['df'].columns
                        x_col = st.selectbox("选择X轴（分类数据）",
                                             options=x_options,
                                             index=0 if len(x_options) > 0 else None,
                                             help="选择包含类别信息的列")

                        # 添加X轴标签设置
                        x_label = st.text_input("X轴标签:", value=x_col if x_col else "",
                                                help="自定义X轴显示文字")

                    with col2:
                        # Y轴选择（数值数据）
                        y_cols = st.multiselect("选择Y轴（数值数据）",
                                                options=numeric_cols,
                                                default=[numeric_cols[0]] if numeric_cols else None,
                                                help="选择一个或多个数值列")

                        # 添加Y轴标签设置
                        y_label = st.text_input("Y轴标签:", value="数值" if y_cols else "",
                                                help="自定义Y轴显示文字")

                    # 分组变量（仅适用于柱状图和折线图）
                    if chart_type in ["柱状图", "折线图"] and other_cols:
                        hue_col = st.selectbox("分组变量（可选）",
                                               options=["无"] + other_cols,
                                               index=0,
                                               help="根据类别分组显示数据")
                        hue_col = None if hue_col == "无" else hue_col
                    else:
                        hue_col = None

                    # 图表生成按钮
                    if st.button("生成图表", key="generate_chart"):
                        if not y_cols:
                            st.warning("请至少选择一个Y轴数据列")
                        else:
                            with st.spinner("正在生成图表..."):
                                try:
                                    # 创建图表容器
                                    with st.container():
                                        st.markdown("#### 数据可视化结果")
                                        fig, ax = plt.subplots(figsize=(10, 6))
                                        plt.style.use('seaborn-v0_8')
                                        plt.grid(True, linestyle='--', alpha=0.3)
                                        plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为SimHei
                                        plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题

                                        # 柱状图
                                        if chart_type == "柱状图" and x_col and y_cols:
                                            # 确保数据是分类类型
                                            if pd.api.types.is_numeric_dtype(st.session_state['df'][x_col]):
                                                st.session_state['df'][x_col] = st.session_state['df'][x_col].astype(
                                                    str)

                                            if len(y_cols) == 1:
                                                # 单Y轴柱状图
                                                sns.barplot(data=st.session_state['df'],
                                                            x=x_col,
                                                            y=y_cols[0],
                                                            hue=hue_col,
                                                            ax=ax,
                                                            palette="Blues_d")
                                                ax.set_ylabel(y_cols[0])
                                            else:
                                                # 多Y轴柱状图处理
                                                plot_df = st.session_state['df'].groupby(x_col)[
                                                    y_cols].mean().reset_index()
                                                plot_df.plot(x=x_col, y=y_cols, kind='bar', ax=ax,
                                                             color=['#4a6baf', '#3a5a9f', '#2a4a8f'])
                                                ax.set_ylabel("平均值")

                                        # 折线图
                                        elif chart_type == "折线图" and x_col and y_cols:
                                            # 确保数据是分类类型
                                            if pd.api.types.is_numeric_dtype(st.session_state['df'][x_col]):
                                                st.session_state['df'][x_col] = st.session_state['df'][x_col].astype(
                                                    str)

                                            for col in y_cols:
                                                sns.lineplot(data=st.session_state['df'],
                                                             x=x_col,
                                                             y=col,
                                                             hue=hue_col,
                                                             ax=ax,
                                                             marker='o',
                                                             linewidth=2.5)
                                            ax.set_ylabel("数值")

                                        # 散点图
                                        elif chart_type == "散点图" and x_col and y_cols and len(y_cols) >= 1:
                                            # 确保使用数值列
                                            if not pd.api.types.is_numeric_dtype(st.session_state['df'][x_col]):
                                                st.warning("散点图X轴需要数值数据")
                                            else:
                                                sns.scatterplot(data=st.session_state['df'],
                                                                x=x_col,
                                                                y=y_cols[0],
                                                                ax=ax,
                                                                s=100,
                                                                color="#4a6baf")
                                                ax.set_ylabel(y_cols[0])

                                        # 饼图
                                        elif chart_type == "饼图" and x_col and y_cols and len(y_cols) == 1:
                                            # 确保数据是分类类型
                                            if pd.api.types.is_numeric_dtype(st.session_state['df'][x_col]):
                                                st.session_state['df'][x_col] = st.session_state['df'][x_col].astype(
                                                    str)

                                            # 聚合数据
                                            plot_df = st.session_state['df'].groupby(x_col)[y_cols[0]].sum()

                                            # 过滤掉空值
                                            plot_df = plot_df[plot_df > 0]

                                            if len(plot_df) > 0:
                                                plot_df.plot(kind='pie',
                                                             autopct='%1.1f%%',
                                                             ax=ax,
                                                             colors=sns.color_palette("Blues", len(plot_df)),
                                                             startangle=90,
                                                             ylabel="")
                                                ax.set_ylabel("")
                                            else:
                                                st.warning("没有有效数据生成饼图")

                                        # 设置图表标题和标签
                                        if x_col and y_cols:
                                            title = f"{chart_type}: {x_col} vs {', '.join(y_cols)}"
                                            if hue_col:
                                                title += f" (按 {hue_col} 分组)"
                                            ax.set_title(title, fontsize=14)

                                            # 设置X轴和Y轴标签（饼图除外）
                                            if chart_type != "饼图":
                                                ax.set_xlabel(x_label, fontsize=12, fontweight='bold', labelpad=10)
                                                ax.set_ylabel(y_label, fontsize=12, fontweight='bold', labelpad=10)

                                                # 添加CSS类名
                                                ax.xaxis.label.set_color('#333')
                                                ax.yaxis.label.set_color('#333')

                                        # 美化图表
                                        plt.xticks(rotation=45, ha='right')
                                        plt.tight_layout()

                                        # 显示图表
                                        st.pyplot(fig)

                                        # 添加数据洞察
                                        if x_col and y_cols:
                                            with st.container():
                                                st.markdown("##### 数据洞察", unsafe_allow_html=True)
                                                insight_text = ""

                                                if chart_type == "柱状图":
                                                    insight_text = f"此柱状图展示了不同 **{x_col}** 类别的 **{', '.join(y_cols)}** 值分布"
                                                elif chart_type == "折线图":
                                                    insight_text = f"此折线图展示了 **{', '.join(y_cols)}** 随时间或类别的变化趋势"
                                                elif chart_type == "散点图":
                                                    insight_text = f"此散点图展示了 **{x_col}** 与 **{y_cols[0]}** 之间的关系"
                                                elif chart_type == "饼图":
                                                    insight_text = f"此饼图展示了不同 **{x_col}** 类别在 **{y_cols[0]}** 中的占比"

                                                if insight_text:
                                                    st.markdown(f'<div class="data-insight">{insight_text}</div>',
                                                                unsafe_allow_html=True)

                                except Exception as e:
                                    st.error(f"图表生成失败: {str(e)}")

# ==================== AI聊天功能 ====================
elif function_selector == "AI聊天":
    # AI聊天功能
    st.subheader("💬 AI聊天助手")

    if not st.session_state['API_KEY']:
        st.warning('请先在侧边栏输入OpenAI API Key！')

    # 显示聊天历史
    for message in st.session_state['messages']:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    # 处理用户输入
    if prompt := st.chat_input("输入您的问题..."):
        if not st.session_state['API_KEY']:
            st.info('请先输入OpenAI API Key！')
            st.stop()

        # 添加用户消息
        st.session_state['messages'].append({'role': 'human', 'content': prompt})

        # 实时显示用户消息
        with st.chat_message("human"):
            st.markdown(prompt)

        with st.spinner('AI正在思考...'):
            try:
                # 创建AI模型
                model = ChatOpenAI(
                    model='gpt-4',
                    api_key=st.session_state['API_KEY'],
                    base_url='https://twapi.openai-hk.com/v1'
                )

                # 创建对话链
                chain = ConversationChain(llm=model, memory=st.session_state['memory'])

                # 获取AI响应
                response = chain.invoke({'input': prompt})['response']

                # 添加AI响应
                st.session_state['messages'].append({'role': 'ai', 'content': response})

                # 实时显示AI响应
                with st.chat_message("ai"):
                    st.markdown(response)

            except Exception as e:
                error_msg = str(e)
                if '402' in error_msg or 'Insufficient Balance' in error_msg:
                    st.error("聊天失败: OpenAI API 余额不足，请充值或检查API密钥")
                else:
                    st.error(f"聊天出错: {error_msg}")
