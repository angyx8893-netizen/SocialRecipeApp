package com.socialrecipeapp.ui.screens.archive

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.socialrecipeapp.domain.repository.RecipeRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

enum class ArchiveSortMode { RECENT, TITLE }

@HiltViewModel
class ArchiveViewModel @Inject constructor(
    private val recipeRepository: RecipeRepository
) : ViewModel() {

    private val _sortMode = MutableStateFlow(ArchiveSortMode.RECENT)
    val sortMode = _sortMode.asStateFlow()

    private val _searchQuery = MutableStateFlow("")
    val searchQuery = _searchQuery.asStateFlow()

    val recipes = combine(_sortMode, _searchQuery) { mode, query ->
        Pair(mode, query)
    }.flatMapLatest { (mode, query) ->
        if (query.isBlank()) {
            if (mode == ArchiveSortMode.RECENT) recipeRepository.getRecipesSortedByRecent()
            else recipeRepository.getRecipesSortedByTitle()
        } else recipeRepository.searchByTitleOrIngredient(query)
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = emptyList()
    )

    fun setSortMode(mode: ArchiveSortMode) {
        _sortMode.value = mode
    }

    fun setSearchQuery(query: String) {
        _searchQuery.value = query
    }
}
