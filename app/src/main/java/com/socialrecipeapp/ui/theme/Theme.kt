package com.socialrecipeapp.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    primary = Coral,
    onPrimary = WarmWhite,
    primaryContainer = CoralLight,
    onPrimaryContainer = OnSurfaceLight,
    secondary = CoralDark,
    onSecondary = WarmWhite,
    secondaryContainer = SecondaryContainerLight,
    onSecondaryContainer = OnSurfaceLight,
    surface = SurfaceLight,
    onSurface = OnSurfaceLight,
    surfaceVariant = WarmWhite,
    onSurfaceVariant = OnSurfaceLight,
    outline = OutlineLight,
    error = ErrorLight,
    onError = WarmWhite
)

private val DarkColorScheme = darkColorScheme(
    primary = CoralLight,
    onPrimary = SurfaceDark,
    primaryContainer = CoralDark,
    onPrimaryContainer = OnSurfaceDark,
    secondary = CoralLight,
    onSecondary = SurfaceDark,
    secondaryContainer = SecondaryContainerDark,
    onSecondaryContainer = OnSurfaceDark,
    surface = SurfaceDark,
    onSurface = OnSurfaceDark,
    surfaceVariant = OutlineDark,
    onSurfaceVariant = OnSurfaceDark,
    outline = OutlineDark,
    error = ErrorDark,
    onError = OnSurfaceDark
)

@Composable
fun SocialRecipeTheme(
    darkTheme: Boolean,
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }
    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
