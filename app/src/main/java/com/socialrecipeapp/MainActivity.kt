package com.socialrecipeapp

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import com.socialrecipeapp.domain.model.ThemeMode
import com.socialrecipeapp.navigation.ImportUrlHolder
import com.socialrecipeapp.navigation.Routes
import com.socialrecipeapp.navigation.SocialRecipeNavGraph
import com.socialrecipeapp.ui.theme.SocialRecipeTheme
import com.socialrecipeapp.ui.theme.SurfaceDark
import com.socialrecipeapp.ui.theme.SurfaceLight
import com.socialrecipeapp.ui.theme.ThemeViewModel
import com.socialrecipeapp.util.extractFirstUrl
import androidx.hilt.navigation.compose.hiltViewModel
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val sharedText = intent?.getStringExtra(Intent.EXTRA_TEXT).orEmpty().trim()
        val urlToImport = extractFirstUrl(sharedText)
        val startDestination = when {
            sharedText.isBlank() -> Routes.Splash
            urlToImport != null -> {
                ImportUrlHolder.set(urlToImport)
                Routes.ImportLoading.createRoute()
            }
            else -> Routes.ImportLinkArgs.createRouteWithInitial(sharedText)
        }

        setContent {
            val themeViewModel: ThemeViewModel = hiltViewModel()
            val themeMode by themeViewModel.themeMode.collectAsState(initial = ThemeMode.SYSTEM)
            val systemDark = isSystemInDarkTheme()
            val useDarkTheme = when (themeMode) {
                ThemeMode.DARK -> true
                ThemeMode.LIGHT -> false
                ThemeMode.SYSTEM -> systemDark
            }
            SocialRecipeTheme(darkTheme = useDarkTheme) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = if (useDarkTheme) SurfaceDark else SurfaceLight
                ) {
                    SocialRecipeNavGraph(
                        startDestination = startDestination
                    )
                }
            }
        }
    }
}
