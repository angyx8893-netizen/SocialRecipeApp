package com.socialrecipeapp.data.repository

import com.socialrecipeapp.data.local.dao.RecipeDao
import com.socialrecipeapp.data.mapper.toDomain
import com.socialrecipeapp.data.mapper.toEntity
import com.socialrecipeapp.domain.model.Recipe
import com.socialrecipeapp.domain.repository.RecipeRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class RecipeRepositoryImpl @Inject constructor(
    private val dao: RecipeDao
) : RecipeRepository {

    override fun getAllRecipes(): Flow<List<Recipe>> =
        dao.getAllByRecent().map { it.map { e -> e.toDomain() } }

    override fun getRecipesSortedByRecent(): Flow<List<Recipe>> =
        dao.getAllByRecent().map { it.map { e -> e.toDomain() } }

    override fun getRecipesSortedByTitle(): Flow<List<Recipe>> =
        dao.getAllByTitle().map { it.map { e -> e.toDomain() } }

    override fun getFavorites(): Flow<List<Recipe>> =
        dao.getFavorites().map { it.map { e -> e.toDomain() } }

    override fun getRecipeById(id: Long): Flow<Recipe?> =
        dao.getById(id).map { it?.toDomain() }

    override fun searchByTitleOrIngredient(query: String): Flow<List<Recipe>> =
        dao.search(query).map { it.map { e -> e.toDomain() } }

    override fun getRecipesByCategory(category: String): Flow<List<Recipe>> =
        dao.getByCategory(category).map { it.map { e -> e.toDomain() } }

    override suspend fun insertRecipe(recipe: Recipe): Long =
        dao.insert(recipe.toEntity())

    override suspend fun updateRecipe(recipe: Recipe) {
        dao.update(recipe.toEntity())
    }

    override suspend fun deleteRecipe(recipe: Recipe) {
        dao.deleteById(recipe.id)
    }

    override suspend fun setFavorite(recipeId: Long, isFavorite: Boolean) {
        dao.setFavorite(recipeId, isFavorite)
    }

    override suspend fun getRecipeBySourceUrl(sourceUrl: String): Recipe? =
        dao.getBySourceUrl(sourceUrl)?.toDomain()
}
