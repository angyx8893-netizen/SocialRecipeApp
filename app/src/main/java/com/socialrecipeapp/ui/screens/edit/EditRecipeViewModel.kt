package com.socialrecipeapp.ui.screens.edit

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.socialrecipeapp.domain.model.IngredientStructured
import com.socialrecipeapp.domain.repository.RecipeRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class EditRecipeState(
    val title: String = "",
    val category: String? = null,
    val ingredientsText: String = "",
    val stepsText: String = "",
    val notes: String? = null,
    val servings: Int? = null,
    val prepTimeMinutes: Int? = null,
    val cookTimeMinutes: Int? = null,
    val recipeId: Long = 0
)

@HiltViewModel
class EditRecipeViewModel @Inject constructor(
    private val recipeRepository: RecipeRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val recipeId: Long = savedStateHandle.get<String>("id")?.toLongOrNull() ?: 0L

    private val _state = MutableStateFlow(EditRecipeState())
    val state = _state.asStateFlow()

    fun load(id: Long) {
        viewModelScope.launch {
            val recipe = recipeRepository.getRecipeById(id).first()
            recipe?.let { r ->
                _state.update {
                    it.copy(
                        title = r.title,
                        category = r.category,
                        ingredientsText = r.ingredientsRaw.joinToString("\n"),
                        stepsText = r.steps.joinToString("\n"),
                        notes = r.notes,
                        servings = r.servings,
                        prepTimeMinutes = r.prepTimeMinutes,
                        cookTimeMinutes = r.cookTimeMinutes,
                        recipeId = r.id
                    )
                }
            }
        }
    }

    fun setTitle(value: String) { _state.update { it.copy(title = value) } }
    fun setCategory(value: String?) { _state.update { it.copy(category = value) } }
    fun setIngredientsText(value: String) { _state.update { it.copy(ingredientsText = value) } }
    fun setStepsText(value: String) { _state.update { it.copy(stepsText = value) } }
    fun setNotes(value: String?) { _state.update { it.copy(notes = value) } }
    fun setServings(value: Int?) { _state.update { it.copy(servings = value) } }
    fun setPrepTimeMinutes(value: Int?) { _state.update { it.copy(prepTimeMinutes = value) } }
    fun setCookTimeMinutes(value: Int?) { _state.update { it.copy(cookTimeMinutes = value) } }

    fun save() {
        viewModelScope.launch {
            val s = _state.value
            val current = recipeRepository.getRecipeById(s.recipeId).first() ?: return@launch
            val updated = current.copy(
                title = s.title.ifBlank { current.title },
                category = s.category ?: current.category,
                ingredientsRaw = s.ingredientsText.lines().map { it.trim() }.filter { it.isNotEmpty() },
                ingredientsStructured = s.ingredientsText.lines().map { it.trim() }.filter { it.isNotEmpty() }
                    .map { IngredientStructured(null, null, it, it) },
                steps = s.stepsText.lines().map { it.trim() }.filter { it.isNotEmpty() },
                notes = s.notes ?: current.notes,
                servings = s.servings ?: current.servings,
                prepTimeMinutes = s.prepTimeMinutes ?: current.prepTimeMinutes,
                cookTimeMinutes = s.cookTimeMinutes ?: current.cookTimeMinutes
            )
            recipeRepository.updateRecipe(updated)
        }
    }
}
