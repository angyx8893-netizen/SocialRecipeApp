package com.socialrecipeapp.domain.model

sealed class ImportState {
    data object Idle : ImportState()
    data object Loading : ImportState()
    data class Success(val recipe: Recipe) : ImportState()
    data class Error(val message: String) : ImportState()
}
