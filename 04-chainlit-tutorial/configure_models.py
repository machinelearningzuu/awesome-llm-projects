import chainlit as cl
from io import BytesIO
import PyPDF2, yaml, os
from cohere import Client
from langchain.vectorstores import Qdrant
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.conversation.memory import ConversationBufferMemory

from langchain.prompts.chat import (
                                    ChatPromptTemplate,
                                    MessagesPlaceholder,
                                    SystemMessagePromptTemplate,
                                    HumanMessagePromptTemplate
                                    )

with open('C:/Work Space/LLM RESEARCH/awesome-llm-projects/cadentials.yaml') as f:
    credentials = yaml.load(f, Loader=yaml.FullLoader)

os.environ["OPENAI_API_TYPE"] = credentials['OPENAI_API_TYPE']
os.environ["OPENAI_API_VERSION"] = credentials['AZURE_OPENAI_VERSION']
os.environ["OPENAI_API_BASE"] = credentials['AZURE_OPENAI_BASE']
os.environ["OPENAI_API_KEY"] = credentials['AZURE_OPENAI_KEY']
os.environ["COHERE_API_KEY"] = credentials['COHERE_API_KEY']

bge_embeddings = HuggingFaceBgeEmbeddings(
                                        model_name="BAAI/bge-small-en-v1.5",
                                        model_kwargs={'device': 'cuda'},
                                        encode_kwargs={'normalize_embeddings': True}
                                        )

llm = AzureChatOpenAI(
                    deployment_name=credentials['AZURE_DEPLOYMENT_NAME'],
                    model_name=credentials['AZURE_ENGINE'],
                    temperature=0.75, 
                    max_tokens=1500
                    )
##################################################################################################


text_splitter = RecursiveCharacterTextSplitter(
                                                chunk_size=1000,
                                                chunk_overlap=100
                                                )

# system_template = """You are a helpful AI assistant and provide the answer for the question asked politely.
# If you don't know the answer, just say that you don't know, don't hallucinate."""

# human_template = "{question}"

# messages = [
#             SystemMessagePromptTemplate.from_template(system_template),
#             MessagesPlaceholder(variable_name="history"),
#             HumanMessagePromptTemplate.from_template(human_template),
#             ]

# prompt = ChatPromptTemplate.from_messages(messages)

# memory = ConversationBufferMemory(
#                                 memory_key="history", 
#                                 return_messages=True
#                                 )

# conversation = LLMChain(
#                         llm=llm, 
#                         verbose=True, 
#                         memory=memory,
#                         prompt=prompt
#                         )

template = """You are a helpful AI assistant and provide the answer for the question asked politely.

------
question: {question}
answer:"""

prompt = PromptTemplate(
                        template=template, 
                        input_variables=["question"]
                        )
llm_chain = LLMChain(
                    prompt=prompt, 
                    llm=llm, 
                    verbose=True
                    )
