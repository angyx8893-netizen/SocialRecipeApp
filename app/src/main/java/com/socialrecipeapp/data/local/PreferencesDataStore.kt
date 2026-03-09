package com.socialrecipeapp.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.socialrecipeapp.domain.model.ThemeMode
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

class PreferencesDataStore @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val prefs = context.dataStore

    /** Backend base URL; when read, normalized (trimmed, with scheme, ending with "/"). */
    val backendBaseUrl: Flow<String> = prefs.data.map { p ->
        normalizeBaseUrl(p[KEY_BACKEND_URL] ?: DEFAULT_BACKEND_URL)
    }

    val themeMode: Flow<ThemeMode> = prefs.data.map { p ->
        when (p[KEY_THEME]) {
            "dark" -> ThemeMode.DARK
            "light" -> ThemeMode.LIGHT
            else -> ThemeMode.SYSTEM
        }
    }

    suspend fun setBackendBaseUrl(url: String) {
        prefs.edit { it[KEY_BACKEND_URL] = normalizeBaseUrl(url) }
    }

    suspend fun setThemeMode(mode: ThemeMode) {
        prefs.edit {
            it[KEY_THEME] = when (mode) {
                ThemeMode.LIGHT -> "light"
                ThemeMode.DARK -> "dark"
                ThemeMode.SYSTEM -> "system"
            }
        }
    }

    companion object {
        private val KEY_BACKEND_URL = stringPreferencesKey("backend_base_url")
        private val KEY_THEME = stringPreferencesKey("theme_mode")
        /** Default for physical device / LAN (normalized with trailing slash). Emulator: http://10.0.2.2:8000/ */
        const val DEFAULT_BACKEND_URL = "http://192.168.1.1:8000/"
    }
}
