# Vector Databases and Embedding Search

Vector databases are specialised storage systems optimised for approximate nearest-neighbour (ANN) search over high-dimensional vector embeddings. They are a core infrastructure component for any system that needs semantic retrieval, including Retrieval-Augmented Generation pipelines.

## How they work

Documents are passed through an embedding model to produce dense vector representations. These vectors are stored in the database alongside the original text. At query time, the query is embedded using the same model, and the database returns the k most similar vectors by cosine or dot-product distance.

Popular options include FAISS (in-memory, Facebook AI), Pinecone (managed cloud), Weaviate (open-source, GraphQL API), and Qdrant (Rust-based, filtering support).

## Relevance to LLMs

Vector databases are most useful when the knowledge base is too large to fit in an LLM context window. By retrieving only the top-k relevant chunks, they enable LLMs to answer grounded questions without seeing the full corpus.
