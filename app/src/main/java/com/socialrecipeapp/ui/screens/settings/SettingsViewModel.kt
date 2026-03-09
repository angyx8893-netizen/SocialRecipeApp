package com.socialrecipeapp.ui.screens.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.socialrecipeapp.data.local.BackendUrlHolder
import com.socialrecipeapp.data.local.normalizeBaseUrl
import com.socialrecipeapp.data.local.PreferencesDataStore
import com.socialrecipeapp.domain.model.ThemeMode
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val preferencesDataStore: PreferencesDataStore
) : ViewModel() {

    private val _backendUrl = MutableStateFlow("")
    val backendUrl = _backendUrl.asStateFlow()

    private val _themeMode = MutableStateFlow(ThemeMode.SYSTEM)
    val themeMode = _themeMode.asStateFlow()

    init {
        viewModelScope.launch {
            _backendUrl.value = preferencesDataStore.backendBaseUrl.first()
            _themeMode.value = preferencesDataStore.themeMode.first()
        }
    }

    /**
     * Saves the backend URL after normalizing: trim, ensure scheme, ensure trailing slash.
     * Blank is kept as-is for validation/error behavior.
     */
    fun setBackendUrl(url: String) {
        val normalized = normalizeBaseUrl(url)
        _backendUrl.value = normalized
        BackendUrlHolder.set(normalized)
        viewModelScope.launch { preferencesDataStore.setBackendBaseUrl(normalized) }
    }

    fun setThemeMode(mode: ThemeMode) {
        _themeMode.value = mode
        viewModelScope.launch { preferencesDataStore.setThemeMode(mode) }
    }
}
