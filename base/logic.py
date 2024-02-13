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

# Load environment variables from .env file
load_dotenv()

# Directory where the Chroma database will be stored
CHROMA_DB_DIRECTORY = "chroma_db/bootstrap_docs"
SCRAPER_LINK_LIMIT = 100


class CustomWebBaseLoader(WebBaseLoader):
    # Custom scraper function to process HTML content
    def _scrape(self, url: str, parser: Union[str, None] = None, bs_kwargs: Optional[dict] = None) -> Any:
        # Fetch the HTML content using the parent class method
        html_content = super()._scrape(url, parser)
        # Find the <main> tag within the HTML content
        main_tag = html_content.find('main')
        # Return the text within the <main> tag, parsed by BeautifulSoup
        return BeautifulSoup(main_tag.text, "html.parser", **(bs_kwargs or {}))

# Check if the database already exists


def database_exists():
    return os.path.exists(CHROMA_DB_DIRECTORY)

# Function to build URLs for scraping


def bootstrap_docs_build_urls():
    # The root URL of Bootstrap documentation
    root_url = "https://getbootstrap.com/docs/5.3/getting-started/contents/"
    # Fetch the content of the root URL
    root_response = requests.get(root_url)
    # Decode the response content
    root_html = root_response.content.decode("utf-8")
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(root_html, 'html.parser')

    # Parse the root URL to extract components
    root_url_parts = urlparse(root_url)
    # Find all links with the specified class attribute
    root_links = soup.find_all(
        "a", attrs={"class": "bd-links-link d-inline-block rounded"})

    # Initialize a set to store unique URLs
    result = set()
    # Limit the number of links to process
    counter = 0
    for root_link in root_links:
        if counter >= SCRAPER_LINK_LIMIT:
            break
        # Get the href attribute of the link
        path = root_link.get("href")
        # Resolve relative paths
        path = str(Path(path).resolve())
        # Remove URL fragments
        path = urlparse(path).path

        # Construct the full URL
        url = f"{root_url_parts.scheme}://{root_url_parts.netloc}{path}"

        # Ensure the URL ends with a slash
        if not url.endswith("/"):
            url = url + "/"

        # Add the URL to the set
        result.add(url)
    # Return the list of unique URLs
    return list(result)

# Function to build the database


def build_database():
    # Get the list of URLs to scrape
    urls = bootstrap_docs_build_urls()
    print(urls)
    # Initialize the custom web loader with the URLs
    loader = CustomWebBaseLoader(urls)
    # Load the documents from the URLs
    documents = loader.load()
    print("documents")
    print(documents)
    # Initialize the text splitter
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=0)
    # Split the documents into chunks
    splits = splitter.split_documents(documents)

    # Initialize the OpenAI embeddings
    embeddings = OpenAIEmbeddings()

    # Build the Chroma database with the document splits and embeddings
    db = Chroma.from_documents(
        splits,
        embeddings,
        collection_name="bootstrap_docs",
        persist_directory=CHROMA_DB_DIRECTORY,
    )
    # Persist the database
    db.persist()

# Function to answer a query using the database
def answer_query(query):
    embeddings = OpenAIEmbeddings() # Get the vector representation for the user question
    db = Chroma( # Fetch the vector collection to compare against the question
        collection_name="bootstrap_docs",
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIRECTORY
    )
    
    chat = ChatOpenAI(temperature=0) 
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=chat, # OpenAI default (gpt-3.5), with low t for more deterministic output
        chain_type="stuff", # LangChain provides shortcuts with prefilled prompts
        retriever=db.as_retriever(), # Use the chroma DB to check for results
        chain_type_kwargs={"verbose": True}  # Log everything
    )
    
    result = chain({"question": query}, return_only_outputs=True)

    return result



