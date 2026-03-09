package com.socialrecipeapp.data.mapper

import com.socialrecipeapp.data.local.entity.ShoppingItemEntity
import com.socialrecipeapp.domain.model.ShoppingItem

fun ShoppingItemEntity.toDomain(): ShoppingItem = ShoppingItem(
    id = id,
    name = name,
    quantity = quantity,
    unit = unit,
    recipeId = recipeId,
    checked = checked,
    addedAt = addedAt
)

fun ShoppingItem.toEntity(): ShoppingItemEntity = ShoppingItemEntity(
    id = id,
    name = name,
    quantity = quantity,
    unit = unit,
    recipeId = recipeId,
    checked = checked,
    addedAt = addedAt
)
