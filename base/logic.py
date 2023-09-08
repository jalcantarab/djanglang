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
from typing import Union, Any
from dotenv import load_dotenv
import os

load_dotenv()

CHROMA_DB_DIRECTORY = "chroma_db/ask_bootstrap_docs"

from bs4 import BeautifulSoup

class CustomWebBaseLoader(WebBaseLoader):
    
    def custom_bs4(self, soup):
        print("====WE'RE PARSING==============")
        """
        Custom BeautifulSoup parser to extract content within the <main> tag.
        """        
        main_tag = soup.find('main') # Find the <main> tag
        return BeautifulSoup(main_tag.text, 'html.parser') if main_tag else ""


    def _scrape(self, url: str, parser: Union[str, None] = None) -> Any:
        print("====WE'RE SCRAPING==============")
        html_content = super()._scrape(url, parser)
        return self.custom_bs4(html_content)

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
    # limit = 4
    # counter = 0
    for root_link in root_links:
        # if counter > limit: 
        #     break
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
    # print(documents)
    text_splitter = CharacterTextSplitter(
        separator = "\n\n",
        chunk_size=750,
        chunk_overlap=0
    )
    splitted_documents = text_splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()

    db = Chroma.from_documents(
        splitted_documents,
        embeddings,
        collection_name="ask_bootstrap_docs",
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



