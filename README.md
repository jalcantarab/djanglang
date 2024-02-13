# Django: LangChained

This is a sample Django application designed to demonstrate the integration of LangChain with Django for building a simple Retrieval-Augmented Generation (RAG) chatbot. This chatbot is capable of answering questions based on the content scraped from a website.

## Overview

The core of Djanglang lies in its ability to:
- Scrape web content from the Bootstrap documentation site.
- Process and index this content into a searchable database using LangChain and Chroma.
- Utilize OpenAI's powerful language models to answer user queries with relevant information extracted from the indexed content.

This project serves as an educational tool for developers looking to explore the intersection of web scraping, natural language processing, and Django web development.

## Features

- **Web Scraping**: Automatically extracts content from specified web pages.
- **Content Indexing**: Processes and stores the scraped content in a searchable format.
- **Content Retrieval**: Matches the user question against the corpus of content.
- **Question Answering**: Leverages an LLM to provide an answer based on the matched content.

## Getting Started

To get started, follow the setup instructions detailed in our [Medium article](https://medium.com/@jakairos/django-langchained-e53aab3ad6bf).

```bash
git clone https://github.com/jalcantarab/djanglang.git
cd djanglang
# Follow setup instructions in the article
```

## Learn More

For a comprehensive guide on how to build, customize, and extend Djanglang, check out our detailed [Medium article](https://medium.com/@jakairos/django-langchained-e53aab3ad6bf). The article covers everything from initial setup to in-depth explanations of the technologies used.

## Contributing

Contributions are welcome! If you have ideas for improvements or want to contribute to the project, please feel free to submit pull requests or open an issue.
