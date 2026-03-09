package com.socialrecipeapp.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.socialrecipeapp.data.local.entity.RecipeEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface RecipeDao {
    @Query("SELECT * FROM recipes ORDER BY importedAt DESC")
    fun getAllByRecent(): Flow<List<RecipeEntity>>

    @Query("SELECT * FROM recipes ORDER BY title COLLATE NOCASE ASC")
    fun getAllByTitle(): Flow<List<RecipeEntity>>

    @Query("SELECT * FROM recipes WHERE isFavorite = 1 ORDER BY importedAt DESC")
    fun getFavorites(): Flow<List<RecipeEntity>>

    @Query("SELECT * FROM recipes WHERE id = :id")
    fun getById(id: Long): Flow<RecipeEntity?>

    @Query("SELECT * FROM recipes WHERE sourceUrl = :url LIMIT 1")
    suspend fun getBySourceUrl(url: String): RecipeEntity?

    @Query("SELECT * FROM recipes WHERE title LIKE '%' || :query || '%' OR ingredientsRawJson LIKE '%' || :query || '%' ORDER BY importedAt DESC")
    fun search(query: String): Flow<List<RecipeEntity>>

    @Query("SELECT * FROM recipes WHERE category = :category ORDER BY importedAt DESC")
    fun getByCategory(category: String): Flow<List<RecipeEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: RecipeEntity): Long

    @Update
    suspend fun update(entity: RecipeEntity)

    @Query("DELETE FROM recipes WHERE id = :id")
    suspend fun deleteById(id: Long)

    @Query("UPDATE recipes SET isFavorite = :isFavorite WHERE id = :id")
    suspend fun setFavorite(id: Long, isFavorite: Boolean)
}
