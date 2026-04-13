from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from py2neo import Graph
from config import *

import os
from dotenv import load_dotenv
load_dotenv()


def _get_siliconflow_kwargs():
    kwargs = {}
    api_key = os.getenv('SILICONFLOW_API_KEY')
    base_url = os.getenv('SILICONFLOW_API_BASE')
    if api_key:
        api_key = api_key.strip().strip('"').strip("'")
    if base_url:
        base_url = base_url.strip().strip('"').strip("'")
    if api_key:
        kwargs['api_key'] = api_key
    if base_url:
        kwargs['base_url'] = base_url
    return kwargs


def _get_float_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_int_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_embeddings_model():
    siliconflow_kwargs = _get_siliconflow_kwargs()
    return OpenAIEmbeddings(
        model=os.getenv('SILICONFLOW_EMBEDDINGS_MODEL', 'BAAI/bge-large-zh-v1.5'),
        **siliconflow_kwargs
    )

def get_llm_model():
    siliconflow_kwargs = _get_siliconflow_kwargs()
    llm_kwargs = {
        'temperature': _get_float_env('TEMPERATURE', 0),
        'max_tokens': _get_int_env('MAX_TOKENS', 1000),
    }
    return ChatOpenAI(
        model=os.getenv('SILICONFLOW_LLM_MODEL', 'deepseek-ai/DeepSeek-V3.2'),
        **llm_kwargs,
        **siliconflow_kwargs
    )


def structured_output_parser(response_schemas):
    text = '''
    Extract entity information from the input text and output it in JSON format,
    including the opening and closing markers "```json" and "```".
    Field definitions and types are listed below. The output JSON must include all fields:\n
    '''
    for schema in response_schemas:
        text += schema.name + ' field, description: ' + schema.description + ', type: ' + schema.type + '\n'
    return text


def replace_token_in_string(string, slots):
    for key, value in slots:
        string = string.replace('%'+key+'%', value)
    return string


def get_neo4j_conn():
    return Graph(
        os.getenv('NEO4J_URI'), 
        auth = (os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )

if __name__ == '__main__':
    llm_model = get_llm_model()
    print(llm_model.predict('vector985: hello 👋'))
