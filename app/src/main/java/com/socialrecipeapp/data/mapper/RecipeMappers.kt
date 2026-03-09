package com.socialrecipeapp.data.mapper

import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.socialrecipeapp.data.local.entity.RecipeEntity
import com.socialrecipeapp.data.remote.dto.IngredientStructuredDto
import com.socialrecipeapp.data.remote.dto.RecipeDto
import com.socialrecipeapp.domain.model.IngredientStructured
import com.socialrecipeapp.domain.model.Recipe

private val gson = Gson()
private val stringListType = object : TypeToken<List<String>>() {}.type
private val ingredientDtoListType = object : TypeToken<List<IngredientStructuredDto>>() {}.type

fun RecipeDto.toDomain(importedAt: Long = System.currentTimeMillis(), isFavorite: Boolean = false): Recipe =
    Recipe(
        id = id ?: 0L,
        sourceUrl = sourceUrl,
        sourcePlatform = sourcePlatform,
        author = author,
        title = title,
        coverImage = coverImage,
        originalLanguage = originalLanguage,
        translatedLanguage = translatedLanguage,
        ingredientsRaw = ingredientsRaw ?: emptyList(),
        ingredientsStructured = (ingredientsStructured ?: emptyList()).map { it.toDomain() },
        steps = steps ?: emptyList(),
        notes = notes,
        servings = servings,
        prepTimeMinutes = prepTimeMinutes,
        cookTimeMinutes = cookTimeMinutes,
        tags = tags ?: emptyList(),
        category = category,
        importedAt = this.importedAt ?: importedAt,
        isFavorite = isFavorite
    )

fun IngredientStructuredDto.toDomain(): IngredientStructured =
    IngredientStructured(quantity = quantity, unit = unit, name = name, originalText = originalText)

fun RecipeEntity.toDomain(): Recipe {
    return Recipe(
        id = id,
        sourceUrl = sourceUrl,
        sourcePlatform = sourcePlatform,
        author = author,
        title = title,
        coverImage = coverImage,
        originalLanguage = originalLanguage,
        translatedLanguage = translatedLanguage,
        ingredientsRaw = parseStringList(ingredientsRawJson),
        ingredientsStructured = parseIngredientList(ingredientsStructuredJson),
        steps = parseStringList(stepsJson),
        notes = notes,
        servings = servings,
        prepTimeMinutes = prepTimeMinutes,
        cookTimeMinutes = cookTimeMinutes,
        tags = parseStringList(tagsJson),
        category = category,
        importedAt = importedAt,
        isFavorite = isFavorite
    )
}

fun Recipe.toEntity(): RecipeEntity = RecipeEntity(
    id = id,
    sourceUrl = sourceUrl,
    sourcePlatform = sourcePlatform,
    author = author,
    title = title,
    coverImage = coverImage,
    originalLanguage = originalLanguage,
    translatedLanguage = translatedLanguage,
    ingredientsRawJson = gson.toJson(ingredientsRaw),
    ingredientsStructuredJson = gson.toJson(ingredientsStructured.map { it.toDto() }),
    stepsJson = gson.toJson(steps),
    notes = notes,
    servings = servings,
    prepTimeMinutes = prepTimeMinutes,
    cookTimeMinutes = cookTimeMinutes,
    tagsJson = gson.toJson(tags),
    category = category,
    importedAt = importedAt,
    isFavorite = isFavorite
)

fun IngredientStructured.toDto(): IngredientStructuredDto =
    IngredientStructuredDto(quantity = quantity, unit = unit, name = name, originalText = originalText)

private fun parseStringList(json: String): List<String> =
    if (json.isBlank()) emptyList() else gson.fromJson(json, stringListType)

private fun parseIngredientList(json: String): List<IngredientStructured> {
    if (json.isBlank()) return emptyList()
    val list: List<IngredientStructuredDto> = gson.fromJson(json, ingredientDtoListType)
    return list.map { it.toDomain() }
}
