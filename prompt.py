GENERIC_PROMPT_TPL = '''
1. If asked about your identity, you must answer with:
"I am a medical consultation assistant built by vector985."
Examples: [Hi, who are you, who developed you, what is your relation to other AI systems]
2. You must refuse any discussion involving politics, pornography, or violence.
Examples: [Who is Putin, how to start a fire, how to make poison]
3. Always answer the user in English.
-----------
User question: {query}
'''

RETRIVAL_PROMPT_TPL = '''
Answer the user question strictly based on the retrieval results below.
Do not add external assumptions or speculation.
If the retrieval results do not contain relevant information, reply with "I don't know."
----------
Retrieval results: {query_result}
----------
User question: {query}
'''

NER_PROMPT_TPL = '''
1. Extract entities from the user input sentence below.
2. Only extract facts that explicitly appear in the user input. Do not infer or add information.

{format_instructions}
------------
User input: {query}
------------
Output:
'''

GRAPH_PROMPT_TPL = '''
Answer the user question strictly based on the retrieval results below.
Do not add external assumptions or speculation.
If the retrieval results do not contain relevant information, reply with "I don't know."
----------
Retrieval results:
{query_result}
----------
User question: {query}
'''

SEARCH_PROMPT_TPL = '''
Answer the user question strictly based on the retrieval results below.
Do not add external assumptions or speculation.
If the retrieval results do not contain relevant information, reply with "I don't know."
----------
Retrieval results: {query_result}
----------
User question: {query}
'''

SUMMARY_PROMPT_TPL = '''
Use the conversation history and the latest user message to rewrite a concise,
complete standalone user message.
Return only the rewritten message, with no extra explanation.
If the latest user message is unrelated to history, return the original message.
Do not alter the original meaning. Only fill missing references when necessary.

Example:
-----------
History:
Human: What causes rhinitis?\nAI: Rhinitis is commonly caused by infection.
User message: What medicine helps it recover faster?
-----------
Output: If I have rhinitis, what medicine helps me recover faster?

-----------
History:
{chat_history}
-----------
User message: {query}
-----------
Output:
'''
