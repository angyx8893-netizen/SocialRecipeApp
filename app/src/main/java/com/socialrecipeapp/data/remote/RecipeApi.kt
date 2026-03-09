package com.socialrecipeapp.data.remote

import com.socialrecipeapp.data.remote.dto.DetectLanguageRequest
import com.socialrecipeapp.data.remote.dto.DetectLanguageResponse
import com.socialrecipeapp.data.remote.dto.ImportRecipeRequest
import com.socialrecipeapp.data.remote.dto.RecipeDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface RecipeApi {
    @GET("health")
    suspend fun health(): Response<Map<String, String>>

    @POST("import-recipe")
    suspend fun importRecipe(@Body request: ImportRecipeRequest): Response<RecipeDto>

    @POST("normalize-recipe")
    suspend fun normalizeRecipe(@Body request: Map<String, Any>): Response<RecipeDto>

    @POST("translate-recipe")
    suspend fun translateRecipe(@Body request: Map<String, Any>): Response<RecipeDto>

    @POST("detect-language")
    suspend fun detectLanguage(@Body request: DetectLanguageRequest): Response<DetectLanguageResponse>
}
