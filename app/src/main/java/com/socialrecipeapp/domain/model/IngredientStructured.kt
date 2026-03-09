package com.socialrecipeapp.domain.model

/**
 * Structured ingredient for shopping list: quantity, unit, name, and original line (fallback).
 */
data class IngredientStructured(
    val quantity: String?,
    val unit: String?,
    val name: String,
    val originalText: String? = null
)
