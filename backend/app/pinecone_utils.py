from pinecone import Pinecone, ServerlessSpec
import pandas as pd
import openai
from dotenv import load_dotenv

import os


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


API_KEY = "pcsk_45rHwF_9JVoNvHY1LVKxrFNmzeVrJKwQ4Mcj4WKoNx5YdeNHRTtA3AXSW8PwzdgTKBHDeu" 
ENVIRONMENT = "us-east1-gcp"  
INDEX_NAME = "recipe-data"
DIMENSION = 1536  

pc = Pinecone(api_key=API_KEY)

if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",  
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

index = pc.Index(INDEX_NAME)

def load_and_prepare_data(filepath: str):
    """
    Load and preprocess the RecipeNLG dataset for embedding and upserting.
    """
    df = pd.read_csv(filepath)

    df["title"] = df["title"].fillna("Unknown Recipe")
    df["ingredients"] = df["ingredients"].fillna("[]") 
    df["directions"] = df["directions"].fillna("[]")  

    def preprocess_row(row):

        ingredients = ", ".join(eval(row["ingredients"]))  
        directions = ". ".join(eval(row["directions"]))  
        return f"{row['title']}. Ingredients: {ingredients}. Directions: {directions}"

    df["text"] = df.apply(preprocess_row, axis=1)

    df["metadata"] = df.apply(
        lambda row: {
            "title": row["title"],
            "ingredients": eval(row["ingredients"]),  
            "directions": eval(row["directions"]),  
            "link": row.get("link", ""),  
            "source": row.get("source", ""),  
        },
        axis=1,
    )

    return df

def generate_and_upsert_embeddings(df, index, batch_size=100, limit=None):
    """
    Generate embeddings and upsert them into Pinecone in batches.
    """
    vectors = []
    total_upserted = 0

    for idx, row in df.iterrows():
        if limit and total_upserted >= limit:
            break

        try:
            response = openai.embeddings.create(model="text-embedding-ada-002",
            input=row["text"])
            embedding = response.data[0].embedding

            vectors.append({
                "id": str(idx),
                "values": embedding,
                "metadata": {
                    "title": row["title"],
                    "ingredients": eval(row["ingredients"]),
                    "directions": eval(row["directions"]),
                    "link": row["link"],
                    "source": row["source"]
                },
            })

            if len(vectors) >= batch_size:
                index.upsert(vectors)
                total_upserted += len(vectors)
                vectors = []  # Clear batch
                print(f"Upserted {total_upserted} embeddings so far...")

        except Exception as e:
            print(f"Error processing row {idx}: {e}")

    if vectors:
        index.upsert(vectors)
        total_upserted += len(vectors)

    print(f"Total embeddings upserted: {total_upserted}")




def get_embedding(text: str) -> list:
    """
    Generate an embedding for a given text using OpenAI API.
    """
    response = openai.Embedding.create(model="text-embedding-ada-002",
    input=text)
    return response.data[0].embedding

def query_index(vector, top_k=10, filter=None):
    """
    Query Pinecone index for similar vectors.
    """
    response = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True,
        filter=filter
    )
    return response.matches

def query_recipes(query_text: str, index, top_k=10):
    """
    Query Pinecone index for recipes similar to the query text.
    """
    try:
        query_embedding = openai.Embedding.create(model="text-embedding-ada-002",
        input=query_text)["data"][0]["embedding"]

        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )

        # Format results
        return [
            {
                "title": match["metadata"]["title"],
                "ingredients": match["metadata"]["ingredients"],
                "link": match["metadata"]["link"],
                "score": match["score"],
            }
            for match in results["matches"]
        ]
    except Exception as e:
        print(f"Error during query: {e}")
        return []


