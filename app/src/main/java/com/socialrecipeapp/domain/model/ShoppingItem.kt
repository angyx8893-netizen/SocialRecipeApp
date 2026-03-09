package com.socialrecipeapp.domain.model

data class ShoppingItem(
    val id: Long,
    val name: String,
    val quantity: String?,
    val unit: String?,
    val recipeId: Long?,
    val checked: Boolean,
    val addedAt: Long
)
