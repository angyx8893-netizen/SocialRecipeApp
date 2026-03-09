package com.socialrecipeapp.util

import android.net.Uri

/**
 * Shared URL utility for the import flow. Single source of truth for normalization and validation.
 *
 * Supported patterns (with or without scheme):
 * - instagram.com, www.instagram.com
 * - tiktok.com, vm.tiktok.com
 * - facebook.com, fb.watch
 * - youtube.com, youtu.be
 * - Any generic http/https link
 */

/**
 * Extracts the first URL from shared text. Trims spaces, then tries the whole string,
 * then splits by whitespace and returns the first token that normalizes to a valid URL.
 *
 * @param text Shared or pasted text that may contain a URL (e.g. "Check this https://instagram.com/p/xxx")
 * @return The first valid URL found, normalized, or null if none
 */
fun extractFirstUrl(text: String): String? {
    val trimmed = text.trim()
    if (trimmed.isBlank()) return null
    val whole = normalizeUrl(trimmed)
    if (isValidUrl(whole)) return whole
    val tokens = trimmed.split(Regex("\\s+"))
    for (token in tokens) {
        val normalized = normalizeUrl(token)
        if (isValidUrl(normalized)) return normalized
    }
    return null
}

/**
 * Normalizes user-entered or shared text into a URL string.
 * - Trims leading/trailing spaces.
 * - Prepends https:// if no scheme is present.
 *
 * @param input Raw input (e.g. "instagram.com/p/xxx", "  https://tiktok.com/...  ")
 * @return Trimmed string with https:// if it had no scheme; otherwise trimmed as-is
 */
fun normalizeUrl(input: String): String {
    val trimmed = input.trim()
    if (trimmed.isBlank()) return trimmed
    return when {
        trimmed.startsWith("http://") || trimmed.startsWith("https://") -> trimmed
        else -> "https://$trimmed"
    }
}

/**
 * Returns true if the input is a valid URL suitable for recipe import.
 * Call after [normalizeUrl] so the string has a scheme.
 *
 * Accepts:
 * - instagram.com, www.instagram.com
 * - tiktok.com, vm.tiktok.com
 * - facebook.com, fb.watch
 * - youtube.com, youtu.be
 * - Any http or https URL with a non-blank host (generic links)
 */
fun isValidUrl(input: String): Boolean {
    if (input.isBlank()) return false
    return try {
        val uri = Uri.parse(input)
        val scheme = uri.scheme
        val host = uri.host
        (scheme == "http" || scheme == "https") && !host.isNullOrBlank()
    } catch (_: Exception) {
        false
    }
}
