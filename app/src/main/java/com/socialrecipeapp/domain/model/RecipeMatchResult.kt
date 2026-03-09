package com.socialrecipeapp.domain.model

/**
 * Result of matching user's available ingredients against a recipe.
 * Used by "Cook with what I have" feature.
 */
data class RecipeMatchResult(
    val recipe: Recipe,
    val matchPercentage: Int,
    val matchedIngredients: List<String>,
    val missingIngredients: List<String>
)
