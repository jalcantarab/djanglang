from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlparse
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from typing import Union, Optional, Any
import requests
import os

load_dotenv()

CHROMA_DB_DIRECTORY = "chroma_db/bootstrap_docs"

class CustomWebBaseLoader(WebBaseLoader):
    def _scrape(self, url: str, parser: Union[str, None] = None, bs_kwargs: Optional[dict] = None) -> Any:
        html_content = super()._scrape(url, parser)
        main_tag = html_content.find('main')  # Find the <main> tag
        return BeautifulSoup(main_tag.text, "html.parser", **(bs_kwargs or {}))

def database_exists():
    return os.path.exists(CHROMA_DB_DIRECTORY)

def bootstrap_docs_build_urls():
    root_url = "https://getbootstrap.com/docs/5.3/getting-started/contents/"
    root_response = requests.get(root_url)
    root_html = root_response.content.decode("utf-8")
    soup = BeautifulSoup(root_html, 'html.parser')

    root_url_parts = urlparse(root_url)
    root_links = soup.find_all("a", attrs={"class": "bd-links-link d-inline-block rounded"})

    result = set()
    limit = 4
    counter = 0
    for root_link in root_links:
        if counter > limit: 
            break
        counter=counter+1
        path = root_link.get("href")
        path = str(Path(path).resolve())
        path = urlparse(path).path  # remove the hashtag

        url = f"{root_url_parts.scheme}://{root_url_parts.netloc}{path}"

        if not url.endswith("/"):
            url = url + "/"

        result.add(url)
    return list(result)

def build_database():
    urls = bootstrap_docs_build_urls()
    print(urls)
    loader = CustomWebBaseLoader(urls)
    documents = loader.load()
    print("documents")
    print(documents)
    splitter =RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, chunk_overlap=0)
    splits = splitter.split_documents(documents)
    # text_splitter = CharacterTextSplitter(
    #     separator = "\n\n",
    #     chunk_size=750,
    #     chunk_overlap=0
    # )
    embeddings = OpenAIEmbeddings()

    db = Chroma.from_documents(
        splits,
        embeddings,
        collection_name="bootstrap_docs",
        persist_directory=CHROMA_DB_DIRECTORY,
    )
    db.persist()

def answer_query(query):
    embeddings = OpenAIEmbeddings()
    db = Chroma(
        collection_name="bootstrap_docs",
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



