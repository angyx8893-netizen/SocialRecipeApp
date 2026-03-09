package com.socialrecipeapp.ui.screens.cookwith

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.socialrecipeapp.domain.model.IngredientStructured
import com.socialrecipeapp.domain.model.Recipe
import com.socialrecipeapp.domain.model.RecipeMatchResult
import com.socialrecipeapp.domain.repository.RecipeRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

/** Filler words to remove when normalizing ingredient names (Italian + English). */
private val FILLER_WORDS = setOf(
    "di", "da", "per", "e", "ed", "a", "al", "alla", "con", "in", "del", "della", "dei", "delle",
    "the", "a", "an", "and", "or", "with", "for", "of", "to", "q.b.", "qb"
)

/**
 * Normalize ingredient name for comparison: lowercase, trim, remove filler words, collapse spaces.
 */
private fun normalizeIngredientName(input: String): String {
    var s = input.trim().lowercase()
    if (s.isEmpty()) return s
    FILLER_WORDS.forEach { word ->
        val regex = "\\b${Regex.escape(word)}\\b".toRegex()
        s = s.replace(regex, " ")
    }
    return s.replace(Regex("\\s+"), " ").trim()
}

/**
 * Base form for singular/plural tolerance: strip common plural endings so "patate" and "patata" can match.
 * English: -s, -es. Italian: -e, -i. Only when word is long enough to avoid false positives.
 */
private fun baseFormForPlural(normalized: String): String {
    if (normalized.length < 3) return normalized
    return when {
        normalized.endsWith("es") && normalized.length > 4 -> normalized.dropLast(2)
        normalized.endsWith("s") && normalized.length > 3 -> normalized.dropLast(1)
        (normalized.endsWith("e") || normalized.endsWith("i")) && normalized.length > 3 -> normalized.dropLast(1)
        else -> normalized
    }
}

/** True if user and recipe normalized strings match (substring or base-form overlap for plural tolerance). */
private fun matchesIngredient(userNorm: String, recipeNorm: String): Boolean {
    if (userNorm in recipeNorm || recipeNorm in userNorm) return true
    val userBase = baseFormForPlural(userNorm)
    val recipeBase = baseFormForPlural(recipeNorm)
    if (userBase.length < 2 || recipeBase.length < 2) return false
    return userBase in recipeBase || recipeBase in userBase || userBase == recipeBase
}

/**
 * Get the display name for an ingredient (originalText if present, else quantity + unit + name).
 */
private fun ingredientDisplayName(ing: IngredientStructured): String {
    return ing.originalText?.takeIf { it.isNotBlank() }
        ?: listOfNotNull(ing.quantity, ing.unit, ing.name).joinToString(" ").trim().ifBlank { ing.name }
}

/**
 * Get the text to use for matching: prefer structured name, then originalText.
 */
private fun ingredientMatchName(ing: IngredientStructured): String = ing.name

@HiltViewModel
class CookWithWhatIHaveViewModel @Inject constructor(
    private val recipeRepository: RecipeRepository
) : ViewModel() {

    private val _ingredientsInput = MutableStateFlow("")
    val ingredientsInput = _ingredientsInput.asStateFlow()

    val matches = combine(
        _ingredientsInput,
        recipeRepository.getAllRecipes()
    ) { input, allRecipes ->
        val userLines = input.lines().map { it.trim() }.filter { it.isNotEmpty() }
        val userNormalized = userLines.map { normalizeIngredientName(it) }.filter { it.isNotEmpty() }.toSet()
        if (userNormalized.isEmpty()) return@combine emptyList<RecipeMatchResult>()

        allRecipes.map { recipe ->
            computeMatch(recipe, userNormalized)
        }
            .filter { it.matchedIngredients.isNotEmpty() }
            .sortedByDescending { it.matchPercentage }
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = emptyList()
    )

    private fun computeMatch(recipe: Recipe, userNormalized: Set<String>): RecipeMatchResult {
        val recipeIngredients = if (recipe.ingredientsStructured.isNotEmpty()) {
            recipe.ingredientsStructured
        } else {
            recipe.ingredientsRaw.map { IngredientStructured(null, null, it, it) }
        }
        val matched = mutableListOf<String>()
        val missing = mutableListOf<String>()
        for (ing in recipeIngredients) {
            val matchName = ingredientMatchName(ing)
            val normalized = normalizeIngredientName(matchName)
            if (normalized.isEmpty()) {
                missing.add(ingredientDisplayName(ing))
                continue
            }
            val isMatch = userNormalized.any { user ->
                matchesIngredient(user, normalized)
            }
            if (isMatch) {
                matched.add(ingredientDisplayName(ing))
            } else {
                missing.add(ingredientDisplayName(ing))
            }
        }
        val total = recipeIngredients.size
        val percentage = if (total == 0) 0 else (matched.size * 100 / total).coerceIn(0, 100)
        return RecipeMatchResult(
            recipe = recipe,
            matchPercentage = percentage,
            matchedIngredients = matched,
            missingIngredients = missing
        )
    }

    fun setIngredientsInput(value: String) {
        _ingredientsInput.value = value
    }
}
