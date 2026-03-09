package com.socialrecipeapp.navigation

/**
 * Holder for the URL to import when navigating to ImportLoading screen.
 * Used to avoid encoding/decoding issues with URLs in navigation route path.
 * Set before navigating to import_loading, then getAndClear() when the screen is shown.
 */
object ImportUrlHolder {
    @Volatile
    private var url: String? = null

    fun set(urlToImport: String) {
        url = urlToImport
    }

    /** Returns the URL and clears it so it is only consumed once. */
    fun getAndClear(): String? = synchronized(this) {
        url.also { url = null }
    }
}
