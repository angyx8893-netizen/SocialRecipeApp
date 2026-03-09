package com.socialrecipeapp.ui.screens.importlink

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.socialrecipeapp.util.isValidUrl
import com.socialrecipeapp.util.normalizeUrl
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ImportLinkViewModel @Inject constructor() : ViewModel() {

    private val _url = MutableStateFlow("")
    val url = _url.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error = _error.asStateFlow()

    fun setUrl(value: String) {
        _url.value = value
    }

    fun clearError() {
        _error.value = null
    }

    /**
     * Uses shared UrlUtils only: trim -> normalizeUrl -> isValidUrl.
     * On success passes normalized URL to onResult.
     */
    fun import(onResult: (String?) -> Unit) {
        viewModelScope.launch {
            val raw = _url.value.trim()
            when {
                raw.isBlank() -> {
                    _error.update { "Please enter or paste a link" }
                    onResult(null)
                }
                else -> {
                    val normalized = normalizeUrl(raw)
                    if (!isValidUrl(normalized)) {
                        _error.update { "This doesn't look like a valid link. Use a full URL (e.g. https://…) or a site like Instagram, TikTok, Facebook, YouTube." }
                        onResult(null)
                    } else {
                        _error.update { null }
                        onResult(normalized)
                    }
                }
            }
        }
    }
}
