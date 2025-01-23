from pinecone import Pinecone, ServerlessSpec
import pandas as pd
import openai
import os

# Initialize Pinecone
API_KEY = "pcsk_45rHwF_9JVoNvHY1LVKxrFNmzeVrJKwQ4Mcj4WKoNx5YdeNHRTtA3AXSW8PwzdgTKBHDeu"  # Replace with your Pinecone API key
ENVIRONMENT = "us-east1-gcp"  # Replace with your Pinecone environment
INDEX_NAME = "recipe-data"
DIMENSION = 1536  # Embedding dimension from OpenAI's text-embedding-ada-002 model

# Create an instance of Pinecone
pc = Pinecone(api_key=API_KEY)

# Check if the index exists, otherwise create it
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",  # Metric type for similarity search
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Access the index
index = pc.Index(INDEX_NAME)

def load_and_prepare_data(filepath: str):
    """
    Load and preprocess the RecipeNLG dataset for embedding and upserting.
    """
    # Load the dataset
    df = pd.read_csv(filepath)

    # Fill missing values with placeholders to avoid errors during processing
    df["title"] = df["title"].fillna("Unknown Recipe")
    df["ingredients"] = df["ingredients"].fillna("[]")  # Placeholder for empty ingredients
    df["directions"] = df["directions"].fillna("[]")  # Placeholder for empty directions

    # Preprocess the fields to ensure consistency
    def preprocess_row(row):
        # Convert ingredients and directions from strings to lists
        ingredients = ", ".join(eval(row["ingredients"]))  # Join the list into a single string
        directions = ". ".join(eval(row["directions"]))  # Join the list into a single string
        return f"{row['title']}. Ingredients: {ingredients}. Directions: {directions}"

    # Combine fields into a single text for embedding
    df["text"] = df.apply(preprocess_row, axis=1)

    # Create metadata for upserting
    df["metadata"] = df.apply(
        lambda row: {
            "title": row["title"],
            "ingredients": eval(row["ingredients"]),  # Store as a list
            "directions": eval(row["directions"]),  # Store as a list
            "link": row.get("link", ""),  # Handle missing links gracefully
            "source": row.get("source", ""),  # Handle missing sources gracefully
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
            # Generate embeddings
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=row["text"]
            )
            embedding = response["data"][0]["embedding"]

            # Prepare vector for Pinecone
            vectors.append({
                "id": str(idx),
                "values": embedding,
                "metadata": {
                    "title": row["title"],
                    "ingredients": eval(row["ingredients"]),
                    "directions": eval(row["directions"]),  # Include directions/instructions here
                    "link": row["link"],
                    "source": row["source"]
                },
            })

            # Upsert in batches
            if len(vectors) >= batch_size:
                index.upsert(vectors)
                total_upserted += len(vectors)
                vectors = []  # Clear batch
                print(f"Upserted {total_upserted} embeddings so far...")

        except Exception as e:
            print(f"Error processing row {idx}: {e}")

    # Final upsert for remaining vectors
    if vectors:
        index.upsert(vectors)
        total_upserted += len(vectors)

    print(f"Total embeddings upserted: {total_upserted}")




def get_embedding(text: str) -> list:
    """
    Generate an embedding for a given text using OpenAI API.
    """
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response["data"][0]["embedding"]

def query_index(vector, top_k=20, filter=None):
    """
    Query Pinecone index for similar vectors.
    """
    response = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True,
        filter=filter
    )
    return response["matches"]

# Query for similar recipes
def query_recipes(query_text: str, index, top_k=20):
    """
    Query Pinecone index for recipes similar to the query text.
    """
    try:
        # Generate query embedding
        query_embedding = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=query_text
        )["data"][0]["embedding"]

        # Query Pinecone index
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


