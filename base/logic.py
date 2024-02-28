from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlparse

from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from typing import Union, Optional, Any
from pymongo import MongoClient
import requests
import os

# Load environment variables from .env file
load_dotenv()

# MongoDB setup
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MONGO_URI = os.environ["MONGO_URI"]
DB_NAME = "langchain-test-2"
COLLECTION_NAME = "test"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "vector_index"
EMBEDDING_FIELD_NAME = "embedding"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

SCRAPER_LINK_LIMIT = 5


class CustomWebBaseLoader(WebBaseLoader):
    # Custom scraper function to process HTML content
    def _scrape(self, url: str, parser: Union[str, None] = None, bs_kwargs: Optional[dict] = None) -> Any:
        # Fetch the HTML content using the parent class method
        html_content = super()._scrape(url, parser)
        # Find the <main> tag within the HTML content
        main_tag = html_content.find('main')
        # Return the text within the <main> tag, parsed by BeautifulSoup
        return BeautifulSoup(main_tag.text, "html.parser", **(bs_kwargs or {}))

def database_exists():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    return False

def bootstrap_docs_build_urls():
    print("building URLs")
    root_url = "https://getbootstrap.com/docs/5.3/getting-started/contents/"
    root_response = requests.get(root_url)
    root_html = root_response.content.decode("utf-8")
    soup = BeautifulSoup(root_html, 'html.parser')

    root_url_parts = urlparse(root_url)
    root_links = soup.find_all(
        "a", attrs={"class": "bd-links-link d-inline-block rounded"})

    result = set()
    counter = 0
    for root_link in root_links:
        if counter >= SCRAPER_LINK_LIMIT:
            break
        path = root_link.get("href")
        path = str(Path(path).resolve())
        path = urlparse(path).path

        url = f"{root_url_parts.scheme}://{root_url_parts.netloc}{path}"
        if not url.endswith("/"):
            url += "/"

        result.add(url)
        counter += 1

    return list(result)


def build_database():
    urls = bootstrap_docs_build_urls()
    loader = CustomWebBaseLoader(urls)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    splits = splitter.split_documents(documents)
    print("New Split")

    # embeddings = OpenAIEmbeddings()

    # Insert the documents with embeddings into MongoDB
    # for doc in splits:
    #     doc["embedding"] = embeddings.get_embeddings([doc["content"]])[0]
    #     collection.insert_one(doc)
        

    # insert the documents in MongoDB Atlas Vector Search
    x = MongoDBAtlasVectorSearch.from_documents(
        documents=splits, embedding=OpenAIEmbeddings(disallowed_special=()), collection=collection, index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME
    )


def answer_query(query):
    embeddings = OpenAIEmbeddings()
    vector_search = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding_field_name=EMBEDDING_FIELD_NAME,
        index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
        embedding_function=embeddings
    )

    chat = ChatOpenAI(temperature=0)
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=chat,
        chain_type="stuff",
        retriever=vector_search.as_retriever(),
        chain_type_kwargs={"verbose": True}
    )

    result = chain({"question": query}, return_only_outputs=True)
    return result