package com.socialrecipeapp.data.remote.dto

import com.google.gson.annotations.SerializedName

data class RecipeDto(
    @SerializedName("id") val id: Long? = null,
    @SerializedName("source_url") val sourceUrl: String,
    @SerializedName("source_platform") val sourcePlatform: String,
    @SerializedName("author") val author: String? = null,
    @SerializedName("title") val title: String,
    @SerializedName("cover_image") val coverImage: String? = null,
    @SerializedName("original_language") val originalLanguage: String? = null,
    @SerializedName("translated_language") val translatedLanguage: String? = null,
    @SerializedName("ingredients_raw") val ingredientsRaw: List<String>? = null,
    @SerializedName("ingredients_structured") val ingredientsStructured: List<IngredientStructuredDto>? = null,
    @SerializedName("steps") val steps: List<String>? = null,
    @SerializedName("notes") val notes: String? = null,
    @SerializedName("servings") val servings: Int? = null,
    @SerializedName("prep_time_minutes") val prepTimeMinutes: Int? = null,
    @SerializedName("cook_time_minutes") val cookTimeMinutes: Int? = null,
    @SerializedName("tags") val tags: List<String>? = null,
    @SerializedName("category") val category: String? = null,
    @SerializedName("imported_at") val importedAt: Long? = null,
    @SerializedName("is_favorite") val isFavorite: Boolean? = null
)

data class IngredientStructuredDto(
    @SerializedName("quantity") val quantity: String? = null,
    @SerializedName("unit") val unit: String? = null,
    @SerializedName("name") val name: String,
    @SerializedName("original_text") val originalText: String? = null
)

data class ImportRecipeRequest(
    @SerializedName("url") val url: String
)

data class DetectLanguageRequest(
    @SerializedName("text") val text: String
)

data class DetectLanguageResponse(
    @SerializedName("language") val language: String,
    @SerializedName("confidence") val confidence: Double? = null
)
