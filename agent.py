from utils import *
from config import *
from prompt import *

import os
from urllib.parse import quote_plus

import requests
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.output_parsers import ResponseSchema, StructuredOutputParser


class Agent:
    def __init__(self):
        self.vdb = Chroma(
            persist_directory=os.path.join(os.path.dirname(__file__), './data/db'),
            embedding_function=get_embeddings_model()
        )

    def _invoke_prompt(self, prompt: PromptTemplate, **kwargs):
        llm = get_llm_model()
        prompt_text = prompt.format(**kwargs)
        result = llm.invoke(prompt_text)
        return result.content if hasattr(result, 'content') else str(result)

    def generic_func(self, query):
        prompt = PromptTemplate.from_template(GENERIC_PROMPT_TPL)
        return self._invoke_prompt(prompt, query=query)

    def retrival_func(self, query):
        documents = self.vdb.similarity_search_with_relevance_scores(query, k=5)
        query_result = [doc[0].page_content for doc in documents if doc[1] > 0.7]

        prompt = PromptTemplate.from_template(RETRIVAL_PROMPT_TPL)
        return self._invoke_prompt(
            prompt,
            query=query,
            query_result='\n\n'.join(query_result) if query_result else 'No relevant information found',
        )

    def graph_func(self, query):
        response_schemas = [
            ResponseSchema(type='list', name='disease', description='Disease name entities'),
            ResponseSchema(type='list', name='symptom', description='Symptom entities'),
            ResponseSchema(type='list', name='drug', description='Drug name entities'),
        ]

        output_parser = StructuredOutputParser(response_schemas=response_schemas)
        format_instructions = structured_output_parser(response_schemas)
        ner_prompt = PromptTemplate(
            template=NER_PROMPT_TPL,
            partial_variables={'format_instructions': format_instructions},
            input_variables=['query'],
        )

        try:
            ner_raw = self._invoke_prompt(ner_prompt, query=query)
            ner_result = output_parser.parse(ner_raw)
        except Exception:
            return 'No relevant information found'

        graph_templates = []
        for _, template in GRAPH_TEMPLATE.items():
            slot = template['slots'][0]
            slot_values = ner_result.get(slot, [])
            for value in slot_values:
                graph_templates.append({
                    'question': replace_token_in_string(template['question'], [[slot, value]]),
                    'cypher': replace_token_in_string(template['cypher'], [[slot, value]]),
                    'answer': replace_token_in_string(template['answer'], [[slot, value]]),
                })

        if not graph_templates:
            return 'No relevant information found'

        graph_documents = [
            Document(page_content=template['question'], metadata=template)
            for template in graph_templates
        ]
        db = FAISS.from_documents(graph_documents, get_embeddings_model())
        graph_documents_filter = db.similarity_search_with_relevance_scores(query, k=3)

        query_result = []
        neo4j_conn = get_neo4j_conn()
        for document in graph_documents_filter:
            question = document[0].page_content
            cypher = document[0].metadata['cypher']
            answer = document[0].metadata['answer']
            try:
                result = neo4j_conn.run(cypher).data()
                if result and any(value for value in result[0].values()):
                    answer_str = replace_token_in_string(answer, list(result[0].items()))
                    query_result.append(f'Question: {question}\nAnswer: {answer_str}')
            except Exception:
                continue

        prompt = PromptTemplate.from_template(GRAPH_PROMPT_TPL)
        return self._invoke_prompt(
            prompt,
            query=query,
            query_result='\n\n'.join(query_result) if query_result else 'No relevant information found',
        )

    def search_func(self, query):
        try:
            url = 'https://www.bing.com/search?q=' + quote_plus(query)
            rsp = requests.get(
                url,
                timeout=10,
                headers={
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/124.0.0.0 Safari/537.36'
                    )
                },
            )
            rsp.raise_for_status()
            query_result = rsp.text[:8000]
            prompt = PromptTemplate.from_template(SEARCH_PROMPT_TPL)
            return self._invoke_prompt(prompt, query=query, query_result=query_result)
        except Exception:
            return 'Web search is currently unavailable. Please rely on existing medical knowledge.'

    def query(self, query):
        tools = [
            Tool.from_function(
                name='generic_func',
                func=lambda _: self.generic_func(query),
                description='General QA tool for greetings, identity, and non-specialized scenarios.',
            ),
            Tool.from_function(
                name='retrival_func',
                func=lambda _: self.retrival_func(query),
                description='Retrieval tool for answering questions from the local knowledge base.',
            ),
            Tool.from_function(
                name='graph_func',
                func=lambda _: self.graph_func(query),
                description='Graph tool for disease, symptom, and medication knowledge graph questions.',
            ),
            Tool.from_function(
                name='search_func',
                func=lambda _: self.search_func(query),
                description='Fallback web search tool when other tools cannot answer the question.',
            ),
        ]

        react_prompt = PromptTemplate.from_template(
            """Please answer in English. You can use the following tools:
{tools}

Use the exact format below:
Question: user question
Thought: your reasoning
Action: tool name, must be one of [{tool_names}]
Action Input: input to the selected tool
Observation: tool output
... (you can repeat for multiple rounds)
Thought: I now have the final answer
Final Answer: final response to the user in English

History: {chat_history}
Question: {input}
Thought:{agent_scratchpad}"""
        )

        agent = create_react_agent(llm=get_llm_model(), tools=tools, prompt=react_prompt)
        memory = ConversationBufferMemory(memory_key='chat_history')
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            memory=memory,
            handle_parsing_errors=True,
            max_iterations=6,
            verbose=os.getenv('VERBOSE'),
        )
        try:
            output = agent_executor.invoke({'input': query})['output']
        except Exception:
            return self.generic_func(query)
        if 'Agent stopped due to iteration limit or time limit.' in output:
            return self.generic_func(query)
        return output


if __name__ == '__main__':
    agent = Agent()
    print(agent.query('What investments has xywy.com received?'))
