import json
from datetime import datetime
from openai import OpenAI
from lunar_python import Solar

def get_annual_fortune(year: int):
    print(f"--> [TOOL CALLED] get_annual_fortune(year={year})")
    solar = Solar.fromYmdHms(year, 1, 1, 12, 0, 0)
    lunar = solar.getLunar()
    gz = lunar.getYearInGanZhi()
    wx = lunar.getYearNaYin()
    return json.dumps({
        "year": year,
        "ganzhi": gz,
        "nayin": wx,
        "context": f"当年干支为{gz}，纳音{wx}。你可以结合命主原局进行生克制化分析。"
    })

bazi_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_annual_fortune",
            "description": "当用户问及具体某一年的运势（例如：2026年我会怎么样？我哪一年容易发财？），调用此工具获取该公历年的准确干支和纳音属性组合，从而进行流年命理分析。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "公历年份，格式如 2026"
                    }
                },
                "required": ["year"]
            }
        }
    }
]

api_key = "sk-sp-0b28da8e3f404df182c05d3fd45787a5"
base_url = "https://coding.dashscope.aliyuncs.com/v1"
model = "qwen3.5-plus"

client = OpenAI(api_key=api_key, base_url=base_url)

messages = [
    {"role": "system", "content": "你是一位新中式命理大师，名为「玄冥」。请分析用户。如果用户问具体某一年，调用工具获取干支。"},
    {"role": "user", "content": "你好，师傅，我2028年的运势怎么样？"}
]

print("Starting LLM Request with Tools...")
try:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=bazi_tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    print(f"Model returned: tool_calls={bool(response_message.tool_calls)}")
    
    if response_message.tool_calls:
        messages.append(response_message)
        
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "get_annual_fortune":
                args = json.loads(tool_call.function.arguments)
                tool_result = get_annual_fortune(args.get("year"))
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": tool_result
                })
        
        print("Sending tool result back to model...")
        second_response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False
        )
        print("Final Output:")
        print(second_response.choices[0].message.content)
    else:
        print("Final Output (No Tools):")
        print(response_message.content)
except Exception as e:
    print(f"Error occurred: {e}")
