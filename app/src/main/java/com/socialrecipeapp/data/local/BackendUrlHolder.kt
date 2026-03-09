package com.socialrecipeapp.data.local

/**
 * Holds the current backend base URL for the network client.
 * Updated at app start from PreferencesDataStore and when the user changes it in Settings.
 * Used by the OkHttp interceptor so Retrofit uses the configured URL without rebuilding.
 * Stored value always ends with "/" (normalized) so Retrofit receives a valid base URL.
 */

/**
 * Normalizes the backend base URL before saving or using.
 * - Trims spaces.
 * - If blank, returns "" (caller can handle validation).
 * - Preserves http:// or https://; if missing, prepends http://.
 * - Ensures the URL ends with "/" so Retrofit always receives a valid base URL.
 */
fun normalizeBaseUrl(input: String): String {
    val trimmed = input.trim()
    if (trimmed.isBlank()) return trimmed
    val withScheme = when {
        trimmed.startsWith("http://") || trimmed.startsWith("https://") -> trimmed
        else -> "http://$trimmed"
    }
    return if (withScheme.endsWith("/")) withScheme else "$withScheme/"
}

object BackendUrlHolder {
    @Volatile
    private var currentUrl: String = PreferencesDataStore.DEFAULT_BACKEND_URL

    /** Returns the current base URL (always ends with "/" when non-blank). */
    fun get(): String = currentUrl

    fun set(url: String) {
        currentUrl = normalizeBaseUrl(url)
    }
}
