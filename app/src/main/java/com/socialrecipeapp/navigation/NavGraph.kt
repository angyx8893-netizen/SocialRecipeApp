package com.socialrecipeapp.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.socialrecipeapp.navigation.ImportUrlHolder
import com.socialrecipeapp.ui.screens.archive.ArchiveScreen
import com.socialrecipeapp.ui.screens.cookwith.CookWithWhatIHaveScreen
import com.socialrecipeapp.ui.screens.detail.RecipeDetailScreen
import com.socialrecipeapp.ui.screens.edit.EditRecipeScreen
import com.socialrecipeapp.ui.screens.favorites.FavoritesScreen
import com.socialrecipeapp.ui.screens.home.HomeScreen
import com.socialrecipeapp.ui.screens.importlink.ImportLinkScreen
import com.socialrecipeapp.ui.screens.importloading.ImportLoadingScreen
import com.socialrecipeapp.ui.screens.settings.SettingsScreen
import com.socialrecipeapp.ui.screens.shopping.ShoppingListScreen
import com.socialrecipeapp.ui.screens.splash.SplashScreen

@Composable
fun SocialRecipeNavGraph(
    navController: NavHostController = rememberNavController(),
    startDestination: String = Routes.Splash
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Routes.Splash) {
            SplashScreen(
                onNavigateToHome = { navController.navigate(Routes.Home) { popUpTo(Routes.Splash) { inclusive = true } } },
                onNavigateToImport = { url ->
                    ImportUrlHolder.set(url)
                    navController.navigate(Routes.ImportLoading.createRoute()) { popUpTo(Routes.Splash) { inclusive = true } }
                }
            )
        }
        composable(Routes.Home) {
            HomeScreen(
                onNavigateToImport = { navController.navigate(Routes.ImportLink) },
                onNavigateToArchive = { navController.navigate(Routes.Archive) },
                onNavigateToFavorites = { navController.navigate(Routes.Favorites) },
                onNavigateToShopping = { navController.navigate(Routes.ShoppingList) },
                onNavigateToCookWith = { navController.navigate(Routes.CookWithWhatIHave) },
                onNavigateToSettings = { navController.navigate(Routes.Settings) },
                onNavigateToDetail = { id -> navController.navigate(Routes.RecipeDetail.createRoute(id)) }
            )
        }
        composable(Routes.ImportLink) {
            ImportLinkScreen(
                initialUrl = null,
                onNavigateBack = { navController.popBackStack() },
                onImportStarted = { url ->
                    ImportUrlHolder.set(url)
                    navController.navigate(Routes.ImportLoading.createRoute()) {
                        navController.currentBackStackEntry?.id?.let { id ->
                            popUpTo(id) { inclusive = true }
                        } ?: popUpTo(Routes.ImportLink) { inclusive = true }
                    }
                }
            )
        }
        composable(
            route = Routes.ImportLinkWithInitial,
            arguments = listOf(navArgument(Routes.ImportLinkArgs.ARG_INITIAL) { type = NavType.StringType; defaultValue = "" })
        ) { backStackEntry ->
            val encoded = backStackEntry.arguments?.getString(Routes.ImportLinkArgs.ARG_INITIAL).orEmpty()
            val initialUrl = if (encoded.isEmpty()) null else try {
                java.net.URLDecoder.decode(encoded, "UTF-8")
            } catch (_: Exception) { encoded }
            ImportLinkScreen(
                initialUrl = initialUrl,
                onNavigateBack = { navController.popBackStack() },
                onImportStarted = { url ->
                    ImportUrlHolder.set(url)
                    navController.navigate(Routes.ImportLoading.createRoute()) {
                        navController.currentBackStackEntry?.id?.let { id ->
                            popUpTo(id) { inclusive = true }
                        } ?: popUpTo(Routes.ImportLink) { inclusive = true }
                    }
                }
            )
        }
        composable(Routes.ImportLoading.route) {
            val url = remember { ImportUrlHolder.getAndClear().orEmpty() }
            ImportLoadingScreen(
                initialUrl = url,
                onNavigateBack = { navController.popBackStack() },
                onSuccess = { navController.navigate(Routes.Home) { popUpTo(0) { inclusive = true } } },
                onEditRecipe = { id -> navController.navigate(Routes.EditRecipe.createRoute(id)) { popUpTo(0) { inclusive = true } } }
            )
        }
        composable(Routes.Archive) {
            ArchiveScreen(
                onNavigateBack = { navController.popBackStack() },
                onRecipeClick = { id -> navController.navigate(Routes.RecipeDetail.createRoute(id)) }
            )
        }
        composable(
            route = Routes.RecipeDetail.route,
            arguments = listOf(navArgument(Routes.RecipeDetail.ARG_ID) { type = NavType.StringType })
        ) { backStackEntry ->
            val id = backStackEntry.arguments?.getString(Routes.RecipeDetail.ARG_ID)?.toLongOrNull() ?: 0L
            RecipeDetailScreen(
                recipeId = id,
                onNavigateBack = { navController.popBackStack() },
                onEdit = { rid -> navController.navigate(Routes.EditRecipe.createRoute(rid)) },
                onDelete = { navController.popBackStack() }
            )
        }
        composable(Routes.Favorites) {
            FavoritesScreen(
                onNavigateBack = { navController.popBackStack() },
                onRecipeClick = { id -> navController.navigate(Routes.RecipeDetail.createRoute(id)) }
            )
        }
        composable(
            route = Routes.EditRecipe.route,
            arguments = listOf(navArgument(Routes.EditRecipe.ARG_ID) { type = NavType.StringType })
        ) { backStackEntry ->
            val id = backStackEntry.arguments?.getString(Routes.EditRecipe.ARG_ID)?.toLongOrNull() ?: 0L
            EditRecipeScreen(
                recipeId = id,
                onNavigateBack = { navController.popBackStack() },
                onSaved = { navController.popBackStack() }
            )
        }
        composable(Routes.ShoppingList) {
            ShoppingListScreen(onNavigateBack = { navController.popBackStack() })
        }
        composable(Routes.CookWithWhatIHave) {
            CookWithWhatIHaveScreen(
                onNavigateBack = { navController.popBackStack() },
                onRecipeClick = { id -> navController.navigate(Routes.RecipeDetail.createRoute(id)) }
            )
        }
        composable(Routes.Settings) {
            SettingsScreen(onNavigateBack = { navController.popBackStack() })
        }
    }
}
