package com.socialrecipeapp.ui.screens.importloading

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.socialrecipeapp.data.mapper.toDomain
import com.socialrecipeapp.data.remote.RecipeApi
import com.socialrecipeapp.data.remote.dto.ImportRecipeRequest
import com.socialrecipeapp.domain.model.ImportState
import com.socialrecipeapp.domain.model.Recipe
import com.socialrecipeapp.domain.repository.RecipeRepository
import com.socialrecipeapp.util.isValidUrl
import com.socialrecipeapp.util.normalizeUrl
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ImportLoadingViewModel @Inject constructor(
    private val api: RecipeApi,
    private val recipeRepository: RecipeRepository
) : ViewModel() {

    private val _importState = MutableStateFlow<ImportState>(ImportState.Idle)
    val importState = _importState.asStateFlow()

    /**
     * Uses shared UrlUtils only: trim -> normalizeUrl -> isValidUrl.
     * Sends the normalized URL to the backend.
     */
    fun importFromUrl(url: String) {
        val trimmed = url.trim()
        if (trimmed.isBlank()) {
            _importState.update { ImportState.Error("Invalid URL") }
            return
        }
        val normalized = normalizeUrl(trimmed)
        if (!isValidUrl(normalized)) {
            _importState.update { ImportState.Error("Invalid URL") }
            return
        }
        viewModelScope.launch {
            _importState.update { ImportState.Loading }
            try {
                val response = api.importRecipe(ImportRecipeRequest(normalized))
                if (response.isSuccessful) {
                    val dto = response.body()
                    if (dto != null) {
                        val recipe = dto.toDomain(isFavorite = false)
                        val existing = recipeRepository.getRecipeBySourceUrl(recipe.sourceUrl)
                        val toSave = if (existing != null) {
                            recipe.copy(id = existing.id, isFavorite = existing.isFavorite)
                        } else {
                            recipe.copy(id = 0)
                        }
                        val id = if (toSave.id == 0L) {
                            recipeRepository.insertRecipe(toSave)
                        } else {
                            recipeRepository.updateRecipe(toSave)
                            toSave.id
                        }
                        val saved = toSave.copy(id = id)
                        _importState.update { ImportState.Success(saved) }
                    } else {
                        _importState.update { ImportState.Error("Empty response from server") }
                    }
                } else {
                    _importState.update {
                        ImportState.Error(response.message() ?: "Import failed (${response.code()})")
                    }
                }
            } catch (e: Exception) {
                _importState.update { ImportState.Error(e.message ?: "Network error") }
            }
        }
    }
}
