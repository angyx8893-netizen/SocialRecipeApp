package com.socialrecipeapp.data.repository

import com.socialrecipeapp.data.local.dao.ShoppingDao
import com.socialrecipeapp.data.mapper.toDomain
import com.socialrecipeapp.data.mapper.toEntity
import com.socialrecipeapp.domain.model.ShoppingItem
import com.socialrecipeapp.domain.repository.ShoppingRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject

class ShoppingRepositoryImpl @Inject constructor(
    private val dao: ShoppingDao
) : ShoppingRepository {

    override fun getAllItems(): Flow<List<ShoppingItem>> =
        dao.getAll().map { it.map { e -> e.toDomain() } }

    override suspend fun insertItem(item: ShoppingItem): Long =
        dao.insert(item.toEntity())

    override suspend fun updateItem(item: ShoppingItem) {
        dao.update(item.toEntity())
    }

    override suspend fun deleteItem(item: ShoppingItem) {
        dao.deleteById(item.id)
    }

    override suspend fun setChecked(id: Long, checked: Boolean) {
        dao.setChecked(id, checked)
    }

    override suspend fun clearChecked() {
        dao.clearChecked()
    }
}
