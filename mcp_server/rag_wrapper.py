from typing import List, Dict, Any
import os

class RAGSystem:
    """
    Wrapper per il tuo sistema RAG esistente.
    Adatta questo codice al tuo RAG specifico.
    """
    
    def __init__(self, vector_store_path: str = "data/vector_store"):
        self.vector_store_path = vector_store_path
        self.vector_store = None
        self.embeddings = None
        self._initialize()
    
    def _initialize(self):
        """Inizializza il sistema RAG"""
        try:
            # Esempio con LangChain e ChromaDB
            # Adatta al tuo sistema RAG esistente
            
            from langchain.embeddings import HuggingFaceEmbeddings
            from langchain.vectorstores import Chroma
            
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            # Carica o crea il vector store
            if os.path.exists(self.vector_store_path):
                self.vector_store = Chroma(
                    persist_directory=self.vector_store_path,
                    embedding_function=self.embeddings
                )
                print(f"✓ Vector store caricato da {self.vector_store_path}")
            else:
                print(f"⚠ Vector store non trovato in {self.vector_store_path}")
                self.vector_store = None
                
        except Exception as e:
            print(f"⚠ Errore nell'inizializzazione RAG: {e}")
            self.vector_store = None
    
    async def query(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Interroga il sistema RAG
        
        Args:
            query: Query dell'utente
            top_k: Numero di documenti da recuperare
        
        Returns:
            Risposta del RAG con documenti recuperati
        """
        if self.vector_store is None:
            return {
                "error": "Vector store non inizializzato",
                "query": query
            }
        
        try:
            # Recupera documenti rilevanti
            docs = self.vector_store.similarity_search(query, k=top_k)
            
            # Formatta i risultati
            retrieved_docs = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": getattr(doc, 'score', None)
                }
                for doc in docs
            ]
            
            # Qui puoi aggiungere la logica per generare una risposta
            # usando un LLM con i documenti recuperati
            
            return {
                "query": query,
                "retrieved_documents": retrieved_docs,
                "top_k": top_k
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "query": query
            }
    
    def add_documents(self, texts: List[str], metadatas: List[Dict] = None):
        """
        Aggiunge documenti al vector store
        
        Args:
            texts: Lista di testi da aggiungere
            metadatas: Lista di metadati (opzionale)
        """
        if self.vector_store is None:
            from langchain.vectorstores import Chroma
            self.vector_store = Chroma(
                persist_directory=self.vector_store_path,
                embedding_function=self.embeddings
            )
        
        self.vector_store.add_texts(
            texts=texts,
            metadatas=metadatas
        )
        self.vector_store.persist()
        print(f"✓ Aggiunti {len(texts)} documenti al vector store")
    
    def clear_store(self):
        """Pulisce il vector store"""
        if self.vector_store:
            self.vector_store.delete_collection()
            print("✓ Vector store pulito")
    
    def get_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche sul vector store"""
        if self.vector_store is None:
            return {"error": "Vector store non inizializzato"}
        
        try:
            collection = self.vector_store._collection
            return {
                "document_count": collection.count(),
                "embedding_dimension": len(self.embeddings.embed_query("test"))
            }
        except Exception as e:
            return {"error": str(e)}