import json
from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

PROMPT_TEMPLATE = """你是一位数据分析助手，你的回应内容取决于用户的请求内容，请按照下面的步骤处理用户请求：

1. 思考阶段 (Thought) ：先分析用户请求类型（文字回答/表格/图表），并验证数据类型是否匹配。
2. 行动阶段 (Action) ：根据分析结果选择以下严格对应的格式。
   - 纯文字回答: 
     {"answer": "不超过50个字符的明确答案"}

   - 表格数据：  
     {"table":{"columns":["列名1", "列名2", ...], "data":[["第一行值1", "值2", ...], ["第二行值1", "值2", ...]]}}

   - 柱状图 
     {"bar":{"columns": ["A", "B", "C", ...], "data":[35, 42, 29, ...]}}

   - 折线图 
     {"line":{"columns": ["A", "B", "C", ...], "data": [35, 42, 29, ...]}}

3. 格式校验要求
   - 字符串值必须使用英文双引号
   - 数值类型不得添加引号
   - 确保数组闭合无遗漏

   错误案例：{'columns':['Product', 'Sales'], data:[[A001, 200]]}  
   正确案例：{"columns":["product", "sales"], "data":[["A001", 200]]}

注意：响应数据的"output"中不要有换行符、制表符以及其他格式符号。

当前用户请求："""


def dataframe_agent(df, query):
    try:
        # 直接传递API密钥（仅用于开发和测试）
        model = ChatOpenAI(
            model="gpt-4o-mini",  # 或者使用"gpt-4"如果你有访问权限
            temperature=0,
            openai_api_key="hk-j62h2y1000055562ac31c59fece0175052cb617eef8352e4",  # 替换为你的实际API密钥
            openai_api_base="https://twapi.openai-hk.com/v1"  # 默认使用OpenAI官方API
        )

        agent = create_pandas_dataframe_agent(
            llm=model,
            df=df,
            agent_executor_kwargs={"handle_parsing_errors": True},
            max_iterations=10,
            early_stopping_method='generate',
            allow_dangerous_code=True,
            verbose=True
        )

        prompt = PROMPT_TEMPLATE + query
        response = agent.invoke({"input": prompt})
        return json.loads(response["output"])

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise