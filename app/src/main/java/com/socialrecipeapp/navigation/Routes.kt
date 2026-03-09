package com.socialrecipeapp.navigation

object Routes {

    const val Splash = "splash"
    const val Home = "home"
    /** Base route for import link screen. Use [ImportLink.createRouteWithInitial] when pre-filling from share. */
    const val ImportLink = "import_link"
    const val ImportLinkWithInitial = "import_link?initial={initial}"

    object ImportLinkArgs {
        const val ARG_INITIAL = "initial"
        fun createRouteWithInitial(initial: String): String {
            if (initial.isBlank()) return ImportLink
            val encoded = java.net.URLEncoder.encode(initial, "UTF-8")
            return "import_link?initial=$encoded"
        }
    }
    const val Archive = "archive"
    const val Favorites = "favorites"
    const val ShoppingList = "shopping_list"
    const val CookWithWhatIHave = "cook_with_what_i_have"
    const val Settings = "settings"

    /** URL is passed via [ImportUrlHolder], not in the route, to avoid encoding issues. */
    object ImportLoading {
        const val route = "import_loading"

        fun createRoute(): String = route
    }

    object RecipeDetail {
        const val route = "recipe_detail/{id}"
        const val ARG_ID = "id"

        fun createRoute(id: Long): String {
            return "recipe_detail/$id"
        }
    }

    object EditRecipe {
        const val route = "edit_recipe/{id}"
        const val ARG_ID = "id"

        fun createRoute(id: Long): String {
            return "edit_recipe/$id"
        }
    }
}