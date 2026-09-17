# Retrieval-Augmented Generation

Retrieval-Augmented Generation (RAG) is a technique that combines retrieval systems with large language models. Instead of relying solely on parametric knowledge, RAG retrieves relevant context from an external knowledge base using vector embeddings, then passes that context to the LLM for grounded generation.

## Key components

- **Retriever**: Uses dense vector embeddings to find semantically similar documents.
- **Reader**: An LLM that generates answers conditioned on the retrieved context.
- **Vector store**: A database optimised for approximate nearest-neighbour search (e.g. FAISS, Pinecone).

RAG improves factual accuracy and allows knowledge to be updated without retraining the model.
