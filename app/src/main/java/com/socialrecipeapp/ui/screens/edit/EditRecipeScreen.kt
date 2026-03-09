package com.socialrecipeapp.ui.screens.edit

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditRecipeScreen(
    recipeId: Long,
    onNavigateBack: () -> Unit,
    onSaved: () -> Unit,
    viewModel: EditRecipeViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val scrollState = rememberScrollState()

    LaunchedEffect(recipeId) { viewModel.load(recipeId) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Edit recipe") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(scrollState)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedTextField(
                value = state.title,
                onValueChange = { viewModel.setTitle(it) },
                label = { Text("Title") },
                modifier = Modifier.fillMaxWidth()
            )
            OutlinedTextField(
                value = state.category ?: "",
                onValueChange = { viewModel.setCategory(it.ifBlank { null }) },
                label = { Text("Category") },
                modifier = Modifier.fillMaxWidth()
            )
            OutlinedTextField(
                value = state.ingredientsText,
                onValueChange = { viewModel.setIngredientsText(it) },
                label = { Text("Ingredients (one per line)") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 4
            )
            OutlinedTextField(
                value = state.stepsText,
                onValueChange = { viewModel.setStepsText(it) },
                label = { Text("Steps (one per line)") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 6
            )
            OutlinedTextField(
                value = state.notes ?: "",
                onValueChange = { viewModel.setNotes(it.ifBlank { null }) },
                label = { Text("Notes") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2
            )
            OutlinedTextField(
                value = state.servings?.toString() ?: "",
                onValueChange = { viewModel.setServings(it.toIntOrNull()) },
                label = { Text("Servings") },
                modifier = Modifier.fillMaxWidth()
            )
            OutlinedTextField(
                value = state.prepTimeMinutes?.toString() ?: "",
                onValueChange = { viewModel.setPrepTimeMinutes(it.toIntOrNull()) },
                label = { Text("Prep time (minutes)") },
                modifier = Modifier.fillMaxWidth()
            )
            OutlinedTextField(
                value = state.cookTimeMinutes?.toString() ?: "",
                onValueChange = { viewModel.setCookTimeMinutes(it.toIntOrNull()) },
                label = { Text("Cook time (minutes)") },
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(16.dp))
            Button(
                onClick = {
                    viewModel.save()
                    onSaved()
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Save")
            }
        }
    }
}
