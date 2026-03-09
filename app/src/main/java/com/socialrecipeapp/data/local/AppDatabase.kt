package com.socialrecipeapp.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.socialrecipeapp.data.local.dao.RecipeDao
import com.socialrecipeapp.data.local.dao.ShoppingDao
import com.socialrecipeapp.data.local.entity.RecipeEntity
import com.socialrecipeapp.data.local.entity.ShoppingItemEntity

@Database(
    entities = [RecipeEntity::class, ShoppingItemEntity::class],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun recipeDao(): RecipeDao
    abstract fun shoppingDao(): ShoppingDao
}
