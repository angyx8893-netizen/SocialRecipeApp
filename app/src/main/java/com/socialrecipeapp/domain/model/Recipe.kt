package com.socialrecipeapp.domain.model

data class Recipe(
    val id: Long,
    val sourceUrl: String,
    val sourcePlatform: String,
    val author: String?,
    val title: String,
    val coverImage: String?,
    val originalLanguage: String?,
    val translatedLanguage: String?,
    val ingredientsRaw: List<String>,
    val ingredientsStructured: List<IngredientStructured>,
    val steps: List<String>,
    val notes: String?,
    val servings: Int?,
    val prepTimeMinutes: Int?,
    val cookTimeMinutes: Int?,
    val tags: List<String>,
    val category: String?,
    val importedAt: Long,
    val isFavorite: Boolean
) {
    val totalTimeMinutes: Int?
        get() = listOfNotNull(prepTimeMinutes, cookTimeMinutes).sum().takeIf { it > 0 }
}
