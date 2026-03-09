package com.socialrecipeapp.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "shopping_items")
data class ShoppingItemEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val name: String,
    val quantity: String?,
    val unit: String?,
    val recipeId: Long?,
    val checked: Boolean,
    val addedAt: Long
)
