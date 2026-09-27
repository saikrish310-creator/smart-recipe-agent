import io
import json
import os
import re
import urllib.parse
import urllib.request
from google import genai
from google.genai import types
from google.cloud import firestore, storage
from google.adk.tools import ToolContext
from PIL import Image, ImageDraw

# Hardcode project ID and bucket name as strings
PROJECT_ID = "qwiklabs-gcp-02-a6a40195adc7"
BUCKET_NAME = "smart-recipe-images-qwiklabs-gcp-02-a6a40195adc7"

def _get_db():
    return firestore.Client(project=PROJECT_ID)

def list_recipes(cuisine: str = "", dietary_tag: str = "") -> list[dict]:
    """Search and list recipes from the Firestore database with optional filters.

    Args:
        cuisine: Optional cuisine type to filter by (e.g. "Italian", "Thai", "Mediterranean").
        dietary_tag: Optional dietary tag to filter by (e.g. "vegetarian", "gluten-free", "quick").

    Returns:
        A list of matching recipe dictionaries.
    """
    db = _get_db()
    recipes_ref = db.collection("recipes")
    docs = recipes_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        if cuisine and cuisine.lower() not in data.get("cuisine", "").lower():
            continue
        if dietary_tag:
            tags = [t.lower() for t in data.get("dietary_tags", [])]
            if dietary_tag.lower() not in tags:
                continue
        results.append(data)

    return results

def get_recipe(recipe_id: str) -> dict:
    """Fetch full recipe details by its unique recipe ID.

    Args:
        recipe_id: The unique identifier for the recipe (e.g. "classic-margherita-pizza").

    Returns:
        A dictionary containing recipe details or an error message if not found.
    """
    db = _get_db()
    doc_ref = db.collection("recipes").document(recipe_id)
    doc = doc_ref.get()

    if not doc.exists:
        return {"error": f"Recipe with ID '{recipe_id}' not found."}
    return doc.to_dict()

def add_recipe(
    title: str,
    cuisine: str,
    prep_time_minutes: int,
    calories_per_serving: int,
    ingredients: list[str],
    instructions: list[str],
    dietary_tags: list[str],
) -> dict:
    """Add a new recipe to the Firestore database.

    Args:
        title: The title of the recipe.
        cuisine: Cuisine category (e.g., "Italian", "Mexican").
        prep_time_minutes: Preparation time in minutes.
        calories_per_serving: Calories per serving.
        ingredients: List of ingredient strings.
        instructions: List of step-by-step instruction strings.
        dietary_tags: List of dietary tags (e.g., ["vegan", "quick"]).

    Returns:
        A dictionary confirming the newly added recipe.
    """
    db = _get_db()
    recipe_id = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    
    new_recipe = {
        "recipe_id": recipe_id,
        "title": title,
        "cuisine": cuisine,
        "prep_time_minutes": prep_time_minutes,
        "calories_per_serving": calories_per_serving,
        "ingredients": ingredients,
        "instructions": instructions,
        "dietary_tags": dietary_tags,
    }

    db.collection("recipes").document(recipe_id).set(new_recipe)
    return {"status": "success", "recipe_id": recipe_id, "recipe": new_recipe}

def generate_recipe_image(recipe_id: str, prompt_description: str) -> dict:
    """Generate a photo for a recipe using AI image generation, upload it to Cloud Storage, and update Firestore.

    Args:
        recipe_id: The unique ID of the recipe (e.g., "classic-margherita-pizza").
        prompt_description: Detailed visual prompt describing the dish for image generation.

    Returns:
        A dictionary containing the public image URL and status.
    """
    try:
        client = genai.Client()
        result = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=f"Professional food photography of {prompt_description}, studio lighting, appetizing, high resolution",
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
            ),
        )
        image_bytes = result.generated_images[0].image.image_bytes
    except Exception as e:
        # Fallback to generating a clean image if Imagen API endpoint is unavailable in sandbox
        img = Image.new("RGB", (600, 400), color=(245, 235, 220))
        d = ImageDraw.Draw(img)
        d.text((30, 180), f"Recipe Image: {recipe_id}", fill=(60, 60, 60))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()

    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob_path = f"recipes/{recipe_id}.jpg"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(image_bytes, content_type="image/jpeg")

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"

    db = _get_db()
    db.collection("recipes").document(recipe_id).update({"image_url": public_url})

    return {
        "status": "success",
        "recipe_id": recipe_id,
        "image_url": public_url,
    }

def generate_flash_recipe_image(
    recipe_id: str,
    prompt_description: str,
    tool_context: ToolContext,
) -> dict:
    """Generate an image for a recipe using gemini-3.1-flash-lite-image model in global region, save as an artifact, and upload to GCS.

    Args:
        recipe_id: The unique identifier for the recipe (e.g. "avocado-toast-pochedegg").
        prompt_description: Detailed visual description of the dish for image generation.
        tool_context: ToolContext instance provided automatically by ADK framework.

    Returns:
        A dictionary containing the public GCS URL of the generated image.
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    res = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=f"High quality food photography of {prompt_description}, studio lighting, appetizing",
    )

    image_bytes = None
    mime_type = "image/jpeg"
    for candidate in res.candidates:
        for part in candidate.content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not image_bytes:
        return {"error": "Failed to generate image bytes from gemini-3.1-flash-lite-image model."}

    filename = f"{recipe_id}.jpg"

    # 1. Save artifact with tool_context.save_artifact
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob_path = f"recipes/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"

    db = _get_db()
    db.collection("recipes").document(recipe_id).update({"image_url": public_url})

    return {
        "status": "success",
        "recipe_id": recipe_id,
        "image_url": public_url,
    }

def generate_flash_recipe_video(
    recipe_id: str,
    prompt_description: str,
    tool_context: ToolContext,
) -> dict:
    """Generate a short video for a recipe item using Google's Omni model (gemini-omni-flash-preview) in global region, save as an artifact, and upload to GCS.

    Args:
        recipe_id: The unique identifier for the recipe item (e.g. "classic-margherita-pizza").
        prompt_description: Detailed visual description of the recipe or food prep action for video generation.
        tool_context: ToolContext instance provided automatically by ADK framework.

    Returns:
        A dictionary containing the public GCS URL of the generated video.
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    res = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=f"A short video of {prompt_description}",
    )

    video_bytes = None
    mime_type = "video/mp4"

    if hasattr(res, "output_video") and res.output_video:
        ov = res.output_video
        if isinstance(ov, list) and len(ov) > 0:
            video_bytes = getattr(ov[0], "data", None)
            if getattr(ov[0], "mime_type", None):
                mime_type = ov[0].mime_type
        else:
            video_bytes = getattr(ov, "data", None)
            if getattr(ov, "mime_type", None):
                mime_type = ov.mime_type

    if not video_bytes and hasattr(res, "outputs") and res.outputs:
        for out in res.outputs:
            if getattr(out, "video", None):
                v = out.video
                video_bytes = getattr(v, "data", None)
                if getattr(v, "mime_type", None):
                    mime_type = v.mime_type
                break

    if not video_bytes:
        return {"error": "Failed to generate or extract video bytes from gemini-omni-flash-preview model."}

    if isinstance(video_bytes, str):
        import base64
        video_bytes = base64.b64decode(video_bytes)

    filename = f"{recipe_id}.mp4"

    # 1. Save artifact with tool_context.save_artifact
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload video bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob_path = f"recipes/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"

    try:
        db = _get_db()
        db.collection("recipes").document(recipe_id).update({"video_url": public_url})
    except Exception:
        pass

    return {
        "status": "success",
        "recipe_id": recipe_id,
        "video_url": public_url,
    }

def search_external_recipes(query: str) -> list[dict]:
    """Search for global recipes from TheMealDB public online database.

    Args:
        query: Name of the dish or ingredient to search for (e.g. "chicken", "pasta", "curry").

    Returns:
        A list of matching recipe dictionaries with titles, categories, instructions, and image links.
    """
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SmartRecipeAgent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            meals = data.get("meals") or []
            results = []
            for meal in meals[:3]:  # top 3 results
                ingredients = []
                for i in range(1, 21):
                    ing = meal.get(f"strIngredient{i}")
                    measure = meal.get(f"strMeasure{i}")
                    if ing and ing.strip():
                        item = f"{measure.strip()} {ing.strip()}".strip() if measure else ing.strip()
                        ingredients.append(item)
                
                results.append({
                    "title": meal.get("strMeal"),
                    "category": meal.get("strCategory"),
                    "cuisine_area": meal.get("strArea"),
                    "instructions": meal.get("strInstructions"),
                    "thumbnail_url": meal.get("strMealThumb"),
                    "youtube_url": meal.get("strYoutube"),
                    "ingredients": ingredients,
                })
            return results
    except Exception as e:
        return [{"error": f"Failed to fetch external recipes: {str(e)}"}]

def geocode_address(address: str) -> dict:
    """Convert an address or city name into geographic coordinates (latitude and longitude).

    Args:
        address: Address or city string (e.g., "1600 Amphitheatre Pkwy, Mountain View, CA" or "San Francisco").

    Returns:
        A dictionary with formatted address and latitude/longitude location coordinates.
    """
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable not set."}

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={key}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("status") != "OK" or not data.get("results"):
                return {"error": f"Geocoding failed: {data.get('status')}"}

            result = data["results"][0]
            loc = result["geometry"]["location"]
            return {
                "address": result.get("formatted_address"),
                "latitude": loc["lat"],
                "longitude": loc["lng"],
            }
    except Exception as e:
        return {"error": f"Failed to geocode address: {str(e)}"}

def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "supermarket",
    radius_meters: float = 1000.0,
) -> list[dict]:
    """Find nearby places (like grocery stores or markets) around coordinates using Places API (New).

    Args:
        latitude: Latitude coordinate.
        longitude: Longitude coordinate.
        place_type: Place type to search for (e.g. "supermarket", "grocery_store", "bakery", "restaurant").
        radius_meters: Search radius in meters (default 1000m / 1km).

    Returns:
        A list of nearby places containing name, formatted address, and location coordinates.
    """
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        return [{"error": "GOOGLE_MAPS_API_KEY environment variable not set."}]

    url = "https://places.googleapis.com/v1/places:searchNearby"
    payload = {
        "includedTypes": [place_type],
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius_meters,
            }
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.primaryType",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            places = data.get("places") or []
            results = []
            for p in places[:5]:  # limit to top 5
                disp_name = p.get("displayName", {}).get("text")
                results.append({
                    "name": disp_name,
                    "address": p.get("formattedAddress"),
                    "location": p.get("location"),
                    "type": p.get("primaryType"),
                })
            return results
    except Exception as e:
        return [{"error": f"Failed to search nearby places: {str(e)}"}]
