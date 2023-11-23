import chainlit as cl
from io import BytesIO
import PyPDF2, yaml, os
from cohere import Client
from langchain.vectorstores import Qdrant
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQAWithSourcesChain,RetrievalQA

from langchain.prompts.chat import (
                                    ChatPromptTemplate,
                                    SystemMessagePromptTemplate,
                                    HumanMessagePromptTemplate
                                    )

from langchain.retrievers.document_compressors import CohereRerank
from langchain.retrievers import BM25Retriever,EnsembleRetriever, ContextualCompressionRetriever

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

cohere_client=Client(api_key=os.environ["COHERE_API_KEY"])

compressor = CohereRerank(
                        client=cohere_client,
                        user_agent='langchain'
                        )
##################################################################################################


text_splitter = RecursiveCharacterTextSplitter(
                                                chunk_size=1000,
                                                chunk_overlap=100
                                                )

system_template = """Use the following pieces of context to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
ALWAYS return a "SOURCES" part in your answer.
The "SOURCES" part should be a reference to the source of the document from which you got your answer.

Begin!
 - - - - - - - - 
{summaries}"""

messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{question}"),
            ]
prompt = ChatPromptTemplate.from_messages(messages)
chain_type_kwargs = {"prompt": prompt}