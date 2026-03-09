package com.socialrecipeapp.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "recipes",
    indices = [Index(value = ["sourceUrl"], unique = true)]
)
data class RecipeEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val sourceUrl: String,
    val sourcePlatform: String,
    val author: String?,
    val title: String,
    val coverImage: String?,
    val originalLanguage: String?,
    val translatedLanguage: String?,
    val ingredientsRawJson: String,
    val ingredientsStructuredJson: String,
    val stepsJson: String,
    val notes: String?,
    val servings: Int?,
    val prepTimeMinutes: Int?,
    val cookTimeMinutes: Int?,
    val tagsJson: String,
    val category: String?,
    val importedAt: Long,
    val isFavorite: Boolean
)
