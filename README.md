# 🥗 Smart Recipe Concierge

![Smart Recipe Concierge Demo](demo.gif)

An intelligent AI recipe concierge and culinary assistant built on Google's Agent Development Kit (ADK) and Vertex AI Agent Engine. Smart Recipe Concierge helps users manage saved recipes, search external culinary databases, calculate nutritional information, generate AI food photography and videos, and locate nearby grocery stores for fresh ingredients.

---

## 🚀 Key Features & Implemented Tools

Based on the implemented tools in `app/tools.py` and `app/agent.py`:

- **Firestore Recipe Database (`list_recipes`, `get_recipe`, `add_recipe`)**:
  - Manages saved recipes stored in Google Cloud Firestore (`recipes` collection), retrieving preparation times, ingredients, instructions, and nutritional details.
- **Vertex AI Memory Bank (`VertexAiMemoryBankService`)**:
  - Remembers user dietary preferences, allergies, and cooking history across sessions using ADK memory callbacks and automatic profile preloading.
- **External Recipe Search (`search_external_recipes`)**:
  - Integrates with external culinary APIs (TheMealDB) to fetch authentic global recipes, meal categories, and prep steps.
- **AI Food Photography Generation (`generate_flash_recipe_image` / `generate_recipe_image`)**:
  - Generates high-quality AI images using Google's `gemini-3.1-flash-lite-image` and `imagen-3.0-generate-002` models.
  - Automatically saves images to ADK Playground artifacts and uploads raw bytes to Google Cloud Storage.
- **AI Short Video Generation (`generate_flash_recipe_video`)**:
  - Generates short cooking preview videos using Google's `gemini-omni-flash-preview` model in the `global` region.
  - Uploads video bytes directly to Google Cloud Storage and registers artifacts in the ADK context.
- **Google Maps & Location Services (`find_nearby_places`, `geocode_address`)**:
  - Geocodes user addresses and searches for nearby grocery stores, supermarkets, and specialty food markets using the Google Maps Places API.
- **Interactive A2UI surfaces (`a2ui_callback`)**:
  - Renders rich, interactive UI cards, ingredient lists, and image carousels via the A2UI v0.8 schema manager.

---

## 🛠️ Google Cloud Services & Integrations

- **Vertex AI Agent Engine / Reasoning Engine**: Serverless agent orchestration runtime with A2A protocol support.
- **Vertex AI Memory Bank Service**: Enterprise persistent conversation memory.
- **Google Cloud Firestore**: NoSQL document database for recipe storage.
- **Google Cloud Storage (GCS)**: Public bucket storage for generated media assets.
- **Google Vertex AI Models**: `gemini-2.5-flash`, `gemini-3.1-flash-lite-image`, `imagen-3.0-generate-002`, and `gemini-omni-flash-preview`.
- **Google Maps Platform**: Geocoding and Places API.

---

## 💻 Local Setup & Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Cloud SDK (`gcloud`) with active authentication

### 1. Environment Setup
Clone the repository and install backend dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set required environment variables:
```bash
export GOOGLE_CLOUD_PROJECT="<your-gcp-project-id>"
export GOOGLE_MAPS_API_KEY="<your-google-maps-api-key>"
```

### 2. Running the Agent Locally
Run the ADK agent development server:
```bash
uv run adk web . --port 8080 --reload_agents
```

### 3. Running the Frontend Locally
Navigate to the `frontend/` directory, install Node dependencies, and start the development proxy:
```bash
cd frontend
npm install
export AGENT_DIRECTORY="app"
python main.py
```

---

## 📋 Planned Capabilities (Not Yet Implemented)
- Automated grocery cart checkout and delivery integration.
- Real-time voice interaction during step-by-step cooking mode.
