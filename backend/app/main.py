from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.pinecone_utils import load_and_prepare_data, generate_and_upsert_embeddings, query_index, get_embedding, index
import openai
import os
from pydantic import BaseModel
from typing import List


class MealPlanRequest(BaseModel):
    selected_days: List[str]
    recipes: List[dict]

# Request model
class QueryRequest(BaseModel):
    query_text: str
    

# Initialize OpenAI API
openai.api_key = "sk--Js0uCVHgBXShKQEBk0kbbezmfUSvBhbjZgnmh-NiIT3BlbkFJR5q-SXx7MMj0zFSCh2qduUFzYcMn-KqdJWiNgqVSkA"  # Replace with your OpenAI API key

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/")
def read_root():
    return {"message": "Welcome to the RAG backend!"}

# File path for Recipes data set
DATA_PATH = os.path.join("app", "data", "RecipeNLG_dataset.csv")

# Load and prepare data
try:
    recipes_df = load_and_prepare_data(DATA_PATH)
    print(f"Data loaded successfully. Sample:\n{recipes_df.head()}")
except Exception as e:
    print(f"Error loading data: {e}")


@app.post("/generate_meal_plan/")
def generate_meal_plan(request: MealPlanRequest):
    """
    Generate a meal plan using GPT.
    """
    try:
        # Craft the prompt for OpenAI
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert meal planner. Generate a weekly meal plan based on the following "
                    "days and recipes. For each day, provide three recipe options. Format the output in a clear and structured paragraph."
                ),
            },
            {
                "role": "user",
                "content": f"Selected days: {', '.join(request.selected_days)}\n\n"
                           f"Recipe options:\n" +
                           "\n".join(
                               f"- {recipe['name']}"
                               for recipe in request.recipes
                           ),
            },
        ]

        # Call OpenAI's chat-based API
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-4"
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )

        # Extract the generated meal plan
        meal_plan = response['choices'][0]['message']['content'].strip()

        return {"meal_plan": meal_plan}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating meal plan: {str(e)}")


# Endpoint to upsert embeddings into Pinecone
@app.post("/upsert/")
def upsert_embeddings():
    """
    Upsert embeddings into the Pinecone index.
    """
    try:
        generate_and_upsert_embeddings(recipes_df, index)
        return {"message": "Embeddings upserted successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error upserting embeddings: {str(e)}")

# Endpoint to query Pinecone for similar recipes
@app.post("/query/")
def query_recipes(request: QueryRequest):
    print(f"Received query_text: {request.query_text}") 
    """
    Query the Pinecone index for similar recipes.
    """
    try:
        query_embedding = get_embedding(request.query_text)

        results = query_index(vector=query_embedding, top_k=20)

        formatted_results = [
            {
                "id": match["id"],
                "score": match["score"],
                "name": match["metadata"]["name"],
                "ingredients": match["metadata"]["ingredients"],
                "steps": match["metadata"]["steps"],
            }
            for match in results
        ]
        return {"results": formatted_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying recipes: {str(e)}")
    
    