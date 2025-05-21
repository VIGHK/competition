from typing import Optional,Union,List,Literal
from pydantic import BaseModel, Field
import json
from openai import OpenAI
import os
import re
from pathlib import Path

input_folder = "input_files"
output_folder_raw = "output_results_raw"
output_folder_nlp = "output_results_nlp"

test ="input_files/test.txt"
with open(test, 'r', encoding='utf-8') as file:
    test_text = file.read()

os.makedirs(output_folder_raw, exist_ok=True)
os.makedirs(output_folder_nlp, exist_ok=True)

#global_subject = "Inkblot Weather"
'''
# 按段落分块，并且保留前后段落的部分信息作为上下文
chunks = []
paragraphs = privacy_policy_text.split('\n\n')
for i in range(len(paragraphs)):
    if i == 0:
        chunk = paragraphs[i] + ' ' + paragraphs[i + 1][:100]
    elif i == len(paragraphs) - 1:
        chunk = paragraphs[i - 1][-100:] + ' ' + paragraphs[i]
    else:
        chunk = paragraphs[i - 1][-100:] + ' ' + paragraphs[i] + ' ' + paragraphs[i + 1][:100]
    chunks.append(chunk)
'''

system_prompt = """"You are a professional privacy policy information extraction assistant. Please extract all structured information from the text following these rules:

**Output Requirements**:
1. Must return a JSON array where each element contains:
   - subject: App/service name (e.g., "WeChat").If not explicitly mentioned, try to infer from the context. For example, if the text mentions "our app" or "we", assume the subject is the name of the app/service related to the privacy policy.
   - action: Data operation verb (must use English like "collect", "share", "analyze", "use").If the action is not clear, try to summarize the data - related operation.
   - privacy_information: Data type (English, e.g., "name", "email", "location", "Android ID").If not specified, try to infer based on the context.
   - third_party: Third-party name (English, e.g., "Google") or null
2. All fields must use exact these names: subject, action, privacy_information, third_party
3. Missing fields should be null
4. All output must be in English

**Example**:
input：“Wechat collect and use your advertising ID and share it with JingDong.Bur it dose not collect your phone number and system time. ”
output：
```json
[
    {"subject": "Wechat", "action": "collect","privacy_information"："advertising ID","third_party":null},
    {"subject": "Wechat", "action": "use","privacy_information"："advertising ID","third_party":null},
    {"subject": "Wechat", "action": "share","privacy_information"："advertising ID","third_party":"JingDong"},
    {"subject": "Wechat", "action": "not collect","privacy_information"："phone number","third_party":null},
    {"subject": "Wechat", "action": "collect","privacy_information"："system time","third_party":"JingDong"}
]
```"""

MAX_CHUNK_LENGTH=5000

class Policy(BaseModel):
    """
    Information about a privacy policy.
    This class is used to extract structured information from a privacy policy text.
    """
    subject: Optional[Union[str, List[str]]] = Field(default=None, description="The subject of the privacy policy, such as the entity or service.")
    action: Optional[Union[str, List[str]]] = Field(default=None, description="The action in the privacy policy, e.g., collection, sharing.")
    privacy_information: Optional[Union[str, List[str]]] = Field(default=None, description="The type of privacy information involved, like personal data, location data.")
    third_party: Optional[Union[str, List[str]]] = Field(default=None, description="The third-party involved in the sharing or collection, if any.")

def safe_get(data, key, default=None):
    return data.get(key, default) or default

client = OpenAI(api_key="sk-4d765424d2a44527a9d7f6193623343a", base_url="https://api.deepseek.com/v1")

PolicyMode = Literal["raw", "with_policylint"]
def process_policy(privacy_policy_text,subject=None,is_chunk=None,mode:PolicyMode="raw"):
    #删除空格和特殊字符
    privacy_policy_text = re.sub(r'\s+', ' ', privacy_policy_text).strip()
    privacy_policy_text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', privacy_policy_text)
    all_results = []

    if mode is "with_policylint":


    #使用分块处理
    if(is_chunk):
        chunks = [privacy_policy_text[i:i + MAX_CHUNK_LENGTH] for i in range(0, len(privacy_policy_text), MAX_CHUNK_LENGTH)]
        for chunk in chunks:
            #补充主体信息
            if "subject" not in chunk:
                chunk = f"{subject}: {chunk}"

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt_def},
                    {"role": "user", "content": chunk}
                ],
                response_format={"type": "json_object"},
                stream=False,
                temperature=0.3  #降低随机性
            )

            try:
                content = response.choices[0].message.content
                print("Debug - Raw API response:", content)
                result = json.loads(content)
                if isinstance(result, str):
                    result = json.loads(result)
                if isinstance(result, dict):
                    result = [result]

                for key, value in result[0].items():
                    all_results.extend(value)

            except json.JSONDecodeError:
                print("Failed to parse the response as JSON.")
            except Exception as e:
                print(f"An error occurred: {e}")
    #不分段处理
    else:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt_def},
                {"role": "user", "content": privacy_policy_text}
            ],
            response_format={"type": "json_object"},
            stream=False,
            temperature=0.3  # 降低随机性
        )
        try:
            content = response.choices[0].message.content
            print("Debug - Raw API response:", content)
            result = json.loads(content)
            if isinstance(result, str):
                result = json.loads(result)
            if isinstance(result, dict):
                result = [result]

            for key, value in result[0].items():
                all_results.extend(value)

        except json.JSONDecodeError:
            print("Failed to parse the response as JSON.")
        except Exception as e:
            print(f"An error occurred: {e}")

    policies = []
    for item in all_results:
        try:
            policy_data = {
                "subject": item.get("subject"),
                "action": item.get("action"),
                "privacy_information": item.get("privacy_information"),
                "third_party": item.get("third_party")
            }
            policy = Policy(**policy_data)
            policies.append(policy)
        except Exception as e:
            print(f"Error parsing item: {item}\nError: {e}")
            continue

    # 生成元组列表
    tuples_list = [
        (policy.subject, policy.action, policy.privacy_information, policy.third_party)
        for policy in policies
    ]

    return tuples_list

txt_files =[f for f in Path(input_folder).glob("*.txt")]

for txt_file in txt_files:
    print(f"\nProcessing file: {txt_file.name}")

    file_subject = txt_file.stem.replace("_", " ")
    with open(txt_file, 'r', encoding='utf-8') as file:
        policy_text = file.read()

    tuples_list = process_policy(policy_text,file_subject)
    output_file_raw = Path(output_folder_raw) / f"{txt_file.stem}_result_raw.txt"

    with open(output_file_raw, 'w', encoding='utf-8') as file:
        for t in tuples_list:
            formatted_tuple = '(' + ','.join(str(item) if item is not None else 'None' for item in t) + ')'
            file.write(formatted_tuple + '\n')

    output_file_nlp = Path(output_folder_nlp) / f"{txt_file.stem}_result_nlp.txt"
    with open(output_file_nlp, 'w', encoding='utf-8') as file:
        for t in tuples_list:
            subject, action, privacy_info, third_party = t

            # 处理默认值
            subject = subject if subject is not None else "We"
            action = action if action is not None else "collect"
            privacy_info = privacy_info if privacy_info is not None else "some personal information"

            # 构建基础句子
            sentence = f"{subject} {action} {privacy_info}"

            # 处理第三方信息
            if third_party is not None:
                if isinstance(third_party, list):
                    if len(third_party) > 1:
                        third_parties = ", ".join(third_party[:-1]) + " and " + third_party[-1]
                    else:
                        third_parties = third_party[0]
                else:
                    third_parties = third_party
                sentence += f" with {third_parties}"
            # 添加句号并写入
            file.write(sentence.capitalize() + ".\n")  # 确保首字母大写

print(f"Results saved to: {output_folder_raw}")
print(f"Results saved to: {output_folder_nlp}")

