package com.socialrecipeapp.di

import com.socialrecipeapp.data.repository.RecipeRepositoryImpl
import com.socialrecipeapp.data.repository.ShoppingRepositoryImpl
import com.socialrecipeapp.domain.repository.RecipeRepository
import com.socialrecipeapp.domain.repository.ShoppingRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindRecipeRepository(impl: RecipeRepositoryImpl): RecipeRepository

    @Binds
    @Singleton
    abstract fun bindShoppingRepository(impl: ShoppingRepositoryImpl): ShoppingRepository
}
