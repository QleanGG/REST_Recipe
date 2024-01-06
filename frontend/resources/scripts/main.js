const MY_SERVER = 'http://127.0.0.1:5000'


// document.addEventListener("DOMContentLoaded", () => 
const display_recipes = () => {
    axios.get(`${MY_SERVER}/get_recipes`)
        .then(response => {
            const data = response.data;
            let recipes = data.recipes;
            const recipeList = document.getElementById('recipe-list');

            recipeList.innerHTML = '';

            recipes.map(recipe => {
                const card = document.createElement('div');
                card.classList.add('col-md-4');
                card.innerHTML = `
                    <div class="card mb-4">
                        <img class="card-img-top" src="${MY_SERVER}${recipe.image_url}" height="200px" alt="Recipe Image">
                        <div class="card-body">
                            <h5 class="card-title">${recipe.name}</h5>
                            <p class="card-text">${recipe.ingredients}</p>
                            <p class="card-text">Cooking Time: ${recipe.cooking_time}</p>
                            <button class="btn btn-primary btn-edit" onclick="editRecipe(${recipe.id})">Edit</button>
                            <button class="btn btn-danger btn-delete" onclick="deleteRecipe(${recipe.id})">Delete</button>
                        </div>
                    </div>
                `;

                recipeList.appendChild(card);
            });
        });
}

function editRecipe(id) {
    // Navigate to the edit_recipe.html page with the recipe ID as a query parameter
    window.location.href = `./edit_recipe.html?id=${id}`;
}

async function deleteRecipe(id) {
    try {
        await axios.delete(`${MY_SERVER}/delete_recipe/${id}`);
        display_recipes(); // Re-render the recipes after successful deletion
    } catch (error) {
        console.error(error);
    }
}


document.addEventListener("DOMContentLoaded", display_recipes) 