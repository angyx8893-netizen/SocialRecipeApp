package com.socialrecipeapp.ui.screens.shopping

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.socialrecipeapp.domain.model.ShoppingItem
import com.socialrecipeapp.domain.repository.ShoppingRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ShoppingListViewModel @Inject constructor(
    private val shoppingRepository: ShoppingRepository
) : ViewModel() {

    val items = shoppingRepository.getAllItems()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    fun setChecked(id: Long, checked: Boolean) {
        viewModelScope.launch { shoppingRepository.setChecked(id, checked) }
    }

    fun delete(item: ShoppingItem) {
        viewModelScope.launch { shoppingRepository.deleteItem(item) }
    }
}
