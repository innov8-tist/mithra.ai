from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import DocumentCompressorPipeline
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain_classic.prompts import PromptTemplate
from langchain_classic.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
from dotenv import load_dotenv
import os
from typing import List, Tuple, Dict
import asyncio

class RetriverProcess:
    """RAG Processing class for document question answering."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100, docs_dir: str = "public"):
        load_dotenv()
        self.groq_api = os.getenv("GROQ_API_KEY")
        self.gemini_api = os.getenv("GEMINI_API_KEY")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.docs_dir = os.path.join(server_dir, docs_dir)
        
        print(f"Looking for documents in: {self.docs_dir}")  # Debug print
        
        self.llm = ChatGroq(
            api_key=self.groq_api,
            model_name="llama-3.3-70b-versatile",
            temperature=0,
        )
        
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001",api_key=self.gemini_api)
    
    def _create_compression_retriever(self, base_retriever):
        redundant_filter = EmbeddingsRedundantFilter(embeddings=self.embeddings)
        pipeline = DocumentCompressorPipeline(transformers=[redundant_filter])
        return ContextualCompressionRetriever(
            base_compressor=pipeline,
            base_retriever=base_retriever
        )
    
    def _load_and_process_documents(self) -> Tuple[FAISS, List[Document]]:
        try:
            cleaned_docs = []
            
            if not os.path.exists(self.docs_dir):
                raise FileNotFoundError(f"Directory not found: {self.docs_dir}")
            
            files_processed = 0
            for file_name in os.listdir(self.docs_dir):
                file_path = os.path.join(self.docs_dir, file_name)
                
                if not os.path.isfile(file_path):
                    continue
                
               
                if file_name.endswith(".pdf"):
                    loader = PyPDFLoader(file_path)
                    texts = loader.load()
                    print(f"Loaded PDF: {file_name} ({len(texts)} pages)")
                    
                    for doc in texts:
                        new_metadata = {
                            'source': file_name,
                            'page': doc.metadata.get('page', 0) + 1
                        }
                        cleaned_doc = Document(
                            page_content=doc.page_content,
                            metadata=new_metadata
                        )
                        cleaned_docs.append(cleaned_doc)
                    files_processed += 1
            
                elif file_name.endswith((".txt", ".md")):
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    
                    print(f"Loaded text file: {file_name}")
                    cleaned_doc = Document(
                        page_content=text,
                        metadata={
                            "source": file_name,
                            "page": 1
                        }
                    )
                    cleaned_docs.append(cleaned_doc)
                    files_processed += 1
            
            if files_processed == 0:
                raise ValueError(f"No supported files found in {self.docs_dir}")
            
            print(f"Total files processed: {files_processed}")
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            chunks = text_splitter.split_documents(cleaned_docs)
            
            db = FAISS.from_documents(chunks, self.embeddings)
            return db, chunks
            
        except UnicodeDecodeError as e:
            print(f"Error decoding file: {e}")
            raise
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    async def query(self, query: str) -> Dict[str, str]:
        db, chunks = self._load_and_process_documents()
        faiss_retriever = db.as_retriever(search_kwargs={"k": 4})
        bm25_retriever = BM25Retriever.from_documents(chunks, k=4)
        ensemble_retriever = EnsembleRetriever(
            retrievers=[faiss_retriever, bm25_retriever],
            weights=[0.5, 0.5]
        )
        print(ensemble_retriever.invoke("what is my name"))
        template = "You should answer the question based on the context. Context: {context} and Question: {question}"
        prompt = PromptTemplate.from_template(template)
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type='stuff',
            retriever=ensemble_retriever,
            verbose=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        print("Processing query...")
        result = qa_chain.invoke(query)
        print(result)
        return {"result": result['result']}



async def Retriver(query: str):
    processor = RetriverProcess()
    return await processor.query(query) 