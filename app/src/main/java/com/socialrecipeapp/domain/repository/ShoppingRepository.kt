package com.socialrecipeapp.domain.repository

import com.socialrecipeapp.domain.model.ShoppingItem
import kotlinx.coroutines.flow.Flow

interface ShoppingRepository {
    fun getAllItems(): Flow<List<ShoppingItem>>
    suspend fun insertItem(item: ShoppingItem): Long
    suspend fun updateItem(item: ShoppingItem)
    suspend fun deleteItem(item: ShoppingItem)
    suspend fun setChecked(id: Long, checked: Boolean)
    suspend fun clearChecked()
}
