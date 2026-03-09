package com.socialrecipeapp.domain.repository

import com.socialrecipeapp.domain.model.Recipe
import kotlinx.coroutines.flow.Flow

interface RecipeRepository {
    fun getAllRecipes(): Flow<List<Recipe>>
    fun getRecipesSortedByRecent(): Flow<List<Recipe>>
    fun getRecipesSortedByTitle(): Flow<List<Recipe>>
    fun getFavorites(): Flow<List<Recipe>>
    fun getRecipeById(id: Long): Flow<Recipe?>
    fun searchByTitleOrIngredient(query: String): Flow<List<Recipe>>
    fun getRecipesByCategory(category: String): Flow<List<Recipe>>
    suspend fun insertRecipe(recipe: Recipe): Long
    suspend fun updateRecipe(recipe: Recipe)
    suspend fun deleteRecipe(recipe: Recipe)
    suspend fun setFavorite(recipeId: Long, isFavorite: Boolean)
    suspend fun getRecipeBySourceUrl(sourceUrl: String): Recipe?
}
