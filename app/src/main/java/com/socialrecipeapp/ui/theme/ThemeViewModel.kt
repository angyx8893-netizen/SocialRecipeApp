package com.socialrecipeapp.ui.theme

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.socialrecipeapp.data.local.PreferencesDataStore
import com.socialrecipeapp.domain.model.ThemeMode
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

@HiltViewModel
class ThemeViewModel @Inject constructor(
    preferencesDataStore: PreferencesDataStore
) : ViewModel() {

    val themeMode: StateFlow<ThemeMode> =
        preferencesDataStore.themeMode.stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = ThemeMode.SYSTEM
        )
}
