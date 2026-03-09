package com.socialrecipeapp.di

import android.content.Context
import androidx.room.Room
import com.socialrecipeapp.data.local.AppDatabase
import com.socialrecipeapp.data.local.BackendUrlHolder
import com.socialrecipeapp.data.local.PreferencesDataStore
import com.socialrecipeapp.data.local.dao.RecipeDao
import com.socialrecipeapp.data.local.dao.ShoppingDao
import com.socialrecipeapp.data.remote.RecipeApi
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(context, AppDatabase::class.java, "social_recipe_db").build()
    }

    @Provides
    @Singleton
    fun provideRecipeDao(db: AppDatabase): RecipeDao = db.recipeDao()

    @Provides
    @Singleton
    fun provideShoppingDao(db: AppDatabase): ShoppingDao = db.shoppingDao()

    @Provides
    @Singleton
    fun provideRecipeApi(prefs: PreferencesDataStore): RecipeApi {
        val initialUrl = runBlocking { prefs.backendBaseUrl.first() }
        BackendUrlHolder.set(initialUrl)
        val client = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .addInterceptor { chain ->
                val request = chain.request()
                val base = BackendUrlHolder.get().trimEnd('/')
                val path = request.url.encodedPath
                val query = request.url.query
                val newUrlString = "$base$path" + if (query != null) "?$query" else ""
                val newRequest = request.newBuilder().url(newUrlString.toHttpUrl()).build()
                chain.proceed(newRequest)
            }
            .addInterceptor(HttpLoggingInterceptor().apply { setLevel(HttpLoggingInterceptor.Level.BODY) })
            .build()
        return Retrofit.Builder()
            .baseUrl("http://localhost/")
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(RecipeApi::class.java)
    }
}
