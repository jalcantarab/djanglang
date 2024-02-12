from urllib.parse import urlparse, urljoin
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
        # soup.find("div", attrs={"class": "bd-content"})
        main_tag = soup.find('main')  # Find the <main> tag
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
        collection_name="ask_bootstrap_docs",
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


# Addons
def initiate_db_creation(db_name, source_url):
    """
    Initiate the database creation process.
    """
    try:
        # 1. Scrape the provided source URL
        urls = scrape_source_url(source_url)
        
        # 2. Build the database using the scraped URLs
        build_custom_database(db_name, urls)
        
        return True, "Database creation initiated successfully."
    except Exception as e:
        return False, str(e)

def scrape_source_url(source_url):
    """
    Scrape the provided source URL to get a list of relevant URLs.
    This function will only scrape contents of the domain under the specified path.
    """
    base_url = urlparse(source_url)
    response = requests.get(source_url)
    html = response.content.decode("utf-8")
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all anchor tags in the page
    links = soup.find_all("a", href=True)
    
    result = set()

    for link in links:
        # Create an absolute URL
        absolute_link = urljoin(source_url, link["href"])
        link_parts = urlparse(absolute_link)
        
        # Check if the link is from the same domain and is under the specified path
        if link_parts.netloc == base_url.netloc and link_parts.path.startswith(base_url.path):
            result.add(absolute_link)

    return list(result)

def build_custom_database(db_name, urls):
    """
    Build a Chroma database using the provided URLs.
    """
    # Define the directory for Chroma DB based on the provided db_name
    CHROMA_DB_DIRECTORY = f"chroma_db/{db_name}"

    # Load the documents from the URLs
    loader = WebBaseLoader(urls)
    documents = loader.load()

    # Split the documents into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    splitted_documents = text_splitter.split_documents(documents)

    # Create embeddings using OpenAI's API
    embeddings = OpenAIEmbeddings()

    # Build the Chroma database
    db = Chroma.from_documents(
        splitted_documents,
        embeddings,
        collection_name=db_name,
        persist_directory=CHROMA_DB_DIRECTORY,
    )
    db.persist()
