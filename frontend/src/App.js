import React, { useState } from "react"
import axios from "axios"
import "./App.css" // Import the CSS file for styles
import { ingredients } from "./data/ingredients" // Import the ingredients array

function App() {
  const [selectedIngredients, setSelectedIngredients] = useState([]) // Track selected ingredients
  const [selectedDays, setSelectedDays] = useState([]) // Track selected days
  const [expandedCategories, setExpandedCategories] = useState([]) // Track expanded categories
  const [expandedRecipes, setExpandedRecipes] = useState([]) // Track expanded recipes
  const [results, setResults] = useState([]) // Store query results
  const [mealPlan, setMealPlan] = useState("") // Store the generated meal plan
  const [error, setError] = useState(null) // Handle errors
  const [isLoading, setIsLoading] = useState(false) // Track loading state

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
      // Fetch recipes
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

      // Generate meal plan
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
      <h1 className="app-title">RAG Meal Planner</h1>
      <div className="app-container">
        {isLoading ? (
          <div className="loading-spinner">
            <p>Generating Meal Plan...</p>
            <div className="spinner"></div>
          </div>
        ) : (
          <>
            {/* Days of the Week and Categories Section */}
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
                      {day[0]}
                    </button>
                  ))}
                </div>
              </div>

              {categories.map((category) => (
                <div key={category} className="category">
                  <h3
                    className="category-header"
                    onClick={() => toggleCategory(category)}
                  >
                    {category}
                  </h3>
                  {expandedCategories.includes(category) && (
                    <div className="ingredients-list">
                      {ingredients
                        .filter(
                          (ingredient) => ingredient.category === category
                        )
                        .map((ingredient) => (
                          <button
                            key={ingredient.item_id}
                            className={`ingredient-button ${
                              selectedIngredients.includes(ingredient.name)
                                ? "selected"
                                : ""
                            }`}
                            onClick={() => toggleIngredient(ingredient.name)}
                          >
                            {ingredient.name}
                          </button>
                        ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Meal Plan and Results Section */}
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
                  <p>{mealPlan}</p>
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
                        {result.name}
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
                              {result.steps.map((step, idx) => (
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
