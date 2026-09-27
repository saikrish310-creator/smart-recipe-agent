import os
from google.cloud import firestore

# Hardcode project ID as a string for Firestore client
PROJECT_ID = "qwiklabs-gcp-02-a6a40195adc7"

def seed_recipes():
    db = firestore.Client(project=PROJECT_ID)
    recipes_ref = db.collection("recipes")

    recipes = [
        {
            "recipe_id": "classic-margherita-pizza",
            "title": "Classic Margherita Pizza",
            "cuisine": "Italian",
            "prep_time_minutes": 25,
            "calories_per_serving": 450,
            "ingredients": ["Pizza dough", "Tomato sauce", "Fresh mozzarella", "Fresh basil", "Olive oil"],
            "instructions": ["Roll out dough", "Spread tomato sauce", "Add mozzarella slices", "Bake at 450F for 12 mins", "Garnish with fresh basil"],
            "dietary_tags": ["vegetarian"],
        },
        {
            "recipe_id": "avocado-toast-pochedegg",
            "title": "Avocado Toast with Poached Egg",
            "cuisine": "Breakfast/American",
            "prep_time_minutes": 10,
            "calories_per_serving": 320,
            "ingredients": ["Sourdough bread", "Ripe avocado", "Eggs", "Lemon juice", "Chili flakes", "Salt"],
            "instructions": ["Toast sourdough bread", "Mash avocado with lemon juice and salt", "Spread onto toast", "Poach egg for 3 mins and place on top", "Sprinkle chili flakes"],
            "dietary_tags": ["vegetarian", "quick"],
        },
        {
            "recipe_id": "thai-green-curry",
            "title": "Thai Green Chicken Curry",
            "cuisine": "Thai",
            "prep_time_minutes": 30,
            "calories_per_serving": 520,
            "ingredients": ["Chicken breast", "Green curry paste", "Coconut milk", "Bamboo shoots", "Thai basil", "Fish sauce"],
            "instructions": ["Sauté green curry paste in coconut cream", "Add sliced chicken and cook through", "Pour in coconut milk and bamboo shoots", "Simmer for 15 mins", "Stir in Thai basil"],
            "dietary_tags": ["gluten-free"],
        },
        {
            "recipe_id": "quinoa-buddha-bowl",
            "title": "Mediterranean Quinoa Buddha Bowl",
            "cuisine": "Mediterranean",
            "prep_time_minutes": 20,
            "calories_per_serving": 410,
            "ingredients": ["Cooked quinoa", "Chickpeas", "Cucumber", "Cherry tomatoes", "Feta cheese", "Kalamata olives", "Tahini dressing"],
            "instructions": ["Assemble quinoa in bowl base", "Arrange chickpeas, cucumber, tomatoes, and olives in sections", "Crumble feta over top", "Drizzle with tahini dressing"],
            "dietary_tags": ["vegetarian", "gluten-free"],
        },
    ]

    for item in recipes:
        doc_ref = recipes_ref.document(item["recipe_id"])
        doc_ref.set(item)
        print(f"Seeded recipe: {item['title']} ({item['recipe_id']})")

    print("\nFirestore seeding complete!")

if __name__ == "__main__":
    seed_recipes()
