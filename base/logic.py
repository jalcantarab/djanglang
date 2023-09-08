from urllib.parse import urlparse
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

CHROMA_DB_DIRECTORY = "chroma_db/ask_django_docs"

def database_exists():
    return os.path.exists(CHROMA_DB_DIRECTORY)

def django_docs_build_urls():
    root_url = "https://docs.djangoproject.com/en/4.2/contents/"
    root_response = requests.get(root_url)
    root_html = root_response.content.decode("utf-8")
    soup = BeautifulSoup(root_html, 'html.parser')

    root_url_parts = urlparse(root_url)
    root_links = soup.find_all("a", attrs={"class": "reference internal"})

    result = set()

    for root_link in root_links:
        path = root_url_parts.path + root_link.get("href")
        path = str(Path(path).resolve())
        path = urlparse(path).path  # remove the hashtag

        url = f"{root_url_parts.scheme}://{root_url_parts.netloc}{path}"

        if not url.endswith("/"):
            url = url + "/"

        result.add(url)
    print(result)
    return list(result)

def build_database():
    urls = django_docs_build_urls()
    loader = WebBaseLoader(urls)
    documents = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    splitted_documents = text_splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()

    db = Chroma.from_documents(
        splitted_documents,
        embeddings,
        collection_name="ask_django_docs",
        persist_directory=CHROMA_DB_DIRECTORY,
    )
    db.persist()

def answer_query(query):
    embeddings = OpenAIEmbeddings()
    db = Chroma(
        collection_name="ask_django_docs",
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIRECTORY
    )
    
    chat = ChatOpenAI(temperature=0)
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=chat,
        chain_type="stuff",
        retriever=db.as_retriever(),
        chain_type_kwargs={"verbose": True}
    )
    
    result = chain({"question": query}, return_only_outputs=True)

    return result



