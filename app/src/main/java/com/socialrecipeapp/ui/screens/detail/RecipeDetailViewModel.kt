package com.socialrecipeapp.ui.screens.detail

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.socialrecipeapp.domain.model.ShoppingItem
import com.socialrecipeapp.domain.repository.RecipeRepository
import com.socialrecipeapp.domain.repository.ShoppingRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class RecipeDetailViewModel @Inject constructor(
    private val recipeRepository: RecipeRepository,
    private val shoppingRepository: ShoppingRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val recipeId: Long = savedStateHandle.get<String>("id")?.toLongOrNull() ?: 0L

    val recipe = recipeRepository.getRecipeById(recipeId)
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = null
        )

    fun toggleFavorite() {
        viewModelScope.launch {
            recipe.value?.let { r ->
                recipeRepository.setFavorite(r.id, !r.isFavorite)
            }
        }
    }

    fun delete() {
        viewModelScope.launch {
            recipe.value?.let { recipeRepository.deleteRecipe(it) }
        }
    }

    fun addAllToShoppingList() {
        viewModelScope.launch {
            val r = recipe.value ?: return@launch
            val now = System.currentTimeMillis()
            r.ingredientsStructured.forEach { ing ->
                val name = ing.originalText?.takeIf { it.isNotBlank() }
                    ?: listOfNotNull(ing.quantity, ing.unit, ing.name).joinToString(" ").trim().ifBlank { ing.name }
                shoppingRepository.insertItem(
                    ShoppingItem(0, name, ing.quantity, ing.unit, r.id, false, now)
                )
            }
            if (r.ingredientsStructured.isEmpty()) {
                r.ingredientsRaw.forEach { line ->
                    shoppingRepository.insertItem(
                        ShoppingItem(0, line, null, null, r.id, false, now)
                    )
                }
            }
        }
    }
}
