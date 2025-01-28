import React, { useState } from "react"
import axios from "axios"
import "./App.css"
import { ingredients } from "./data/ingredients"

function App() {
  const [selectedIngredients, setSelectedIngredients] = useState([])
  const [selectedDays, setSelectedDays] = useState([])
  const [expandedCategories, setExpandedCategories] = useState([])
  const [expandedRecipes, setExpandedRecipes] = useState([])
  const [results, setResults] = useState([])
  const [mealPlan, setMealPlan] = useState("")
  const [error, setError] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const capitalizeFirstLetter = (string) =>
    string.charAt(0).toUpperCase() + string.slice(1).toLowerCase()

  const toggleIngredient = (ingredientName) => {
    setSelectedIngredients((prev) =>
      prev.includes(ingredientName)
        ? prev.filter((item) => item !== ingredientName)
        : [...prev, ingredientName]
    )
  }

  const toggleCategory = (category) => {
    setExpandedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((item) => item !== category)
        : [...prev, category]
    )
  }

  const toggleDay = (day) => {
    setSelectedDays((prev) =>
      prev.includes(day) ? prev.filter((item) => item !== day) : [...prev, day]
    )
  }

  const toggleRecipe = (recipeId) => {
    setExpandedRecipes((prev) =>
      prev.includes(recipeId)
        ? prev.filter((id) => id !== recipeId)
        : [...prev, recipeId]
    )
  }

  const handleClearAll = () => {
    setSelectedIngredients([])
    setSelectedDays([])
  }

  const handleGenerateMealPlan = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const queryString = selectedIngredients.join(",")
      const recipeResponse = await axios.post(
        "http://127.0.0.1:8000/query/",
        { query_text: queryString },
        {
          headers: { "Content-Type": "application/json" },
        }
      )

      const recipes = recipeResponse.data.results
      setResults(recipes)

      const mealPlanResponse = await axios.post(
        "http://127.0.0.1:8000/generate_meal_plan/",
        {
          selected_days: selectedDays,
          recipes: recipes,
        },
        {
          headers: { "Content-Type": "application/json" },
        }
      )

      setMealPlan(mealPlanResponse.data.meal_plan)
    } catch (err) {
      console.error("Error generating meal plan:", err)
      setError("Failed to generate meal plan. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const daysOfWeek = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ]
  const categories = [
    "vegetables",
    "fruits",
    "meats",
    "grains",
    "dairy",
    "seafoods",
    "legumes",
    "spices and herbs",
    "oils",
  ]

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">RAG Meal Planner</h1>
      </header>
      <div className="app-container">
        {isLoading ? (
          <div className="loading-spinner">
            <p>Generating Meal Plan</p>
            <div className="spinner"></div>
          </div>
        ) : (
          <>
            <div className="categories-container">
              <button className="clear-button" onClick={handleClearAll}>
                Clear All
              </button>
              <div className="days-container">
                <h3 className="days-header">Select Days</h3>
                <div className="days-list">
                  {daysOfWeek.map((day) => (
                    <button
                      key={day}
                      className={`day-button ${
                        selectedDays.includes(day) ? "selected" : ""
                      }`}
                      onClick={() => toggleDay(day)}
                    >
                      {day}
                    </button>
                  ))}
                </div>
              </div>

              <h3 className="days-header">Select Ingredients</h3>

              {categories.map((category) => (
                <div key={category} className="category">
                  <h3
                    className="category-header"
                    onClick={() => toggleCategory(category)}
                  >
                    {capitalizeFirstLetter(category)}
                    <span>
                      {expandedCategories.includes(category) ? "▼" : "▶"}
                    </span>
                  </h3>
                  {expandedCategories.includes(category) && (
                    <div className="ingredients-list">
                      {ingredients
                        .filter(
                          (ingredient) => ingredient.category === category
                        )
                        .map((ingredient) => (
                          <div
                            key={ingredient.item_id}
                            className={`ingredient-item ${
                              selectedIngredients.includes(ingredient.name)
                                ? "selected"
                                : ""
                            }`}
                            onClick={() => toggleIngredient(ingredient.name)}
                          >
                            <img
                              src={ingredient.img}
                              alt={ingredient.name}
                              className="ingredient-image"
                            />
                            <p className="ingredient-title">
                              {capitalizeFirstLetter(ingredient.name)}
                            </p>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="search-results-container">
              <button
                className="generate-button"
                onClick={handleGenerateMealPlan}
                disabled={
                  selectedIngredients.length === 0 || selectedDays.length === 0
                }
              >
                Generate Weekly Meal Plan
              </button>

              {error && <p className="error-message">{error}</p>}

              {mealPlan && (
                <div className="meal-plan">
                  <h2 className="meal-plan-title">Weekly Meal Plan</h2>
                  {mealPlan
                    .split("\n")
                    .filter((dayPlan) => dayPlan.trim() !== "")
                    .map((dayPlan, idx) => (
                      <div key={idx} className="day-plan">
                        <p>{dayPlan}</p>
                      </div>
                    ))}
                </div>
              )}

              {results.length > 0 && (
                <div className="results-container">
                  <h2 className="results-title">Recommended Recipes</h2>
                  {results.map((result) => (
                    <div className="result-card" key={result.id}>
                      <h3
                        className="result-name"
                        onClick={() => toggleRecipe(result.id)}
                      >
                        {result.title}
                      </h3>
                      {expandedRecipes.includes(result.id) && (
                        <>
                          <div className="result-section">
                            <h4>Ingredients</h4>
                            <ul className="result-ingredients">
                              {result.ingredients.map((ingredient, idx) => (
                                <li key={idx}>{ingredient}</li>
                              ))}
                            </ul>
                          </div>
                          <div className="result-section">
                            <h4>Steps</h4>
                            <ol className="result-steps">
                              {result.directions.map((step, idx) => (
                                <li key={idx}>{step}</li>
                              ))}
                            </ol>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default App
