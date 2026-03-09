package com.socialrecipeapp.ui.screens.importloading

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.socialrecipeapp.domain.model.ImportState

@Composable
fun ImportLoadingScreen(
    initialUrl: String,
    onNavigateBack: () -> Unit,
    onSuccess: () -> Unit,
    onEditRecipe: (Long) -> Unit,
    viewModel: ImportLoadingViewModel = hiltViewModel()
) {
    val state by viewModel.importState.collectAsState()

    LaunchedEffect(initialUrl) {
        viewModel.importFromUrl(initialUrl)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        when (val s = state) {
            is ImportState.Idle,
            is ImportState.Loading -> {
                CircularProgressIndicator(
                    modifier = Modifier.padding(16.dp),
                    color = MaterialTheme.colorScheme.primary
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "Importing recipe…",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }
            is ImportState.Success -> {
                Icon(
                    imageVector = Icons.Default.Check,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = "Recipe imported",
                    style = MaterialTheme.typography.titleLarge,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.height(24.dp))
                Button(onClick = { onEditRecipe(s.recipe.id) }) {
                    Text("Edit recipe")
                }
                Button(onClick = onSuccess, modifier = Modifier.padding(top = 8.dp)) {
                    Text("Go to Home")
                }
            }
            is ImportState.Error -> {
                Text(
                    text = s.message,
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.error
                )
                Spacer(modifier = Modifier.height(24.dp))
                Button(onClick = onNavigateBack) {
                    Text("Back")
                }
            }
        }
    }
}
