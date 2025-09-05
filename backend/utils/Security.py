import json
import os
import requests
import chromadb #type: ignore
from typing import Dict, Any, List
from utils.System import SmartStudentDataSystem

def collect_data():
    ai = SmartStudentDataSystem()
    ai.Autoload_new_data()
    return ai.collections

# standalone_qa_generator.py
"""
A standalone tool to automatically generate a JSON file of question-and-answer pairs
based on a student's profile from the database.
This script is completely independent of ai_analyst.py and can be configured
to run in either ONLINE or OFFLINE mode.
"""

# IMPORTANT!!! Set the desired mode here: 'online' or 'offline'. online for test pero actual talaga offline. i suggest i offline niyo na to try.
#generated_qa_offline.json pag 'offline'
#generated_qa_online.json pag 'online'

MODE = 'offline'

# --- CONFIGURATION ---
# THIS IS WHERE YOU WILL CHANGE THE VALUE, FEED NIYO YUNG PDM ID HERE DAPAT STRING, EDIT NIYO NALANG NUMBER OF QUESTIONS IF GUSTO NIYO
STUDENT_ID_TO_TEST = "PDM-2025-0001"
NUMBER_OF_QUESTIONS = 5
OUTPUT_FILENAME = f"generated_qa_{MODE}.json"
CHROMA_DB_PATH = "./chroma_store" # The path to your ChromaDB database folder

# ==============================
# 1. Standalone Configuration Loader
# ==============================
def load_config(mode: str, config_path: str = "config.json") -> Dict[str, Any]:
    """Loads the specified configuration block ('online' or 'offline') from the config file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            full_config = json.load(f)
            if mode in full_config:
                print(f"✅ Successfully loaded '{mode}' configuration.")
                return full_config[mode]
            else:
                raise KeyError(f"'{mode}' section not found in {config_path}")
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"❌ FATAL: Could not load configuration. Error: {e}")
        return None

# ==============================
# 2. Unified LLM Service
# ==============================
class LLMService:
    """A unified client for interacting with both Mistral (online) and Ollama (offline) APIs."""
    def __init__(self, config: dict, mode: str):
        self.mode = mode
        if self.mode == 'online':
            self.api_key = config.get("mistral_api_key")
            self.api_url = config.get("mistral_api_url")
            self.model = config.get("synth_model")
        else: # offline
            self.api_url = config.get("ollama_api_url")
            self.model = config.get("synth_model")

    def execute(self, system_prompt: str, user_prompt: str) -> str:
        """Executes a request to the configured LLM API."""
        if not self.api_url or not self.model:
            return '{"error": "API URL or model is not configured."}'

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        
        if self.mode == 'online':
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": self.model, "messages": messages, "response_format": {"type": "json_object"}}
        else: # offline
            headers = {"Content-Type": "application/json"}
            payload = {"model": self.model, "messages": messages, "stream": False, "format": "json"}

        try:
            resp = requests.post(self.api_url, headers=headers, data=json.dumps(payload), timeout=180)
            resp.raise_for_status()
            rj = resp.json()
            if self.mode == 'online':
                return rj['choices'][0]['message']['content'].strip()
            else: # offline
                return rj['message']['content'].strip()
        except Exception as e:
            return f'{{"error": "Failed to connect to AI service: {e}"}}'

# ==============================
# 3. Standalone Database Connector
# ==============================
def get_profile_from_db(pdm_id: str, db_path: str) -> List[dict]:
    """[UPGRADED] Connects to ChromaDB and retrieves a student profile by their ID,
    explicitly excluding grade-related documents."""
    try:
        client = chromadb.PersistentClient(path=db_path)
        all_collections = client.list_collections()
        
        # --- ✨ FIX: Exclude collections with 'grades' in the name ---
        student_collections = [
            c for c in all_collections 
            if 'students' in c.name and 'grades' not in c.name
        ]
        
        id_filter = {"$or": [{"student_id": {"$eq": pdm_id}}, {"student_number": {"$eq": pdm_id}}]}
        all_docs = []
        for collection in student_collections:
            results = collection.get(where=id_filter, include=["metadatas", "documents"])
            for i, doc_content in enumerate(results['documents']):
                all_docs.append({
                    "source_collection": collection.name, 
                    "content": doc_content, 
                    "metadata": results['metadatas'][i]
                })
        return all_docs
    except Exception as e:
        print(f"❌ Database error: Could not connect or query ChromaDB at path '{db_path}'. Error: {e}")
        return []

# ==============================
# 4. Main Q&A Generator Logic
# ==============================
def generate_and_save(pdm_id: str, count: int, llm: LLMService):
    """Retrieves a profile, generates Q&A pairs, and saves them."""
    print("="*50)
    print(f"🚀 Starting Q&A Generation for PDM ID: {pdm_id} (Mode: {llm.mode.upper()})")
    print("="*50)

    # Step 1: Retrieve profile
    print(f"1. Retrieving profile for {pdm_id} from ChromaDB...")
    profile_docs = get_profile_from_db(pdm_id=pdm_id, db_path=CHROMA_DB_PATH)
    if not profile_docs:
        print(f"❌ Could not retrieve a valid profile for {pdm_id}. Aborting.")
        return

    context_str = "\n\n".join([f"Content:\n{doc.get('content')}" for doc in profile_docs])
    print("   ✅ Profile retrieved successfully.")

    # Step 2: Call the AI to generate Q&A
    print(f"2. Asking {llm.mode.upper()} AI to generate {count} question-answer pairs...")
    system_prompt = "You are an expert in creating training data. Your job is to generate a list of question-and-answer pairs based ONLY on the provided text."
    user_prompt = f"""
    Here is a student's profile text:
    ---
    {context_str}
    ---
    Based ONLY on the provided text, act as an interviewer and generate a JSON object with a single key "qa_pairs".
    only ask those in the student profile, do NOT make up any information.
    focus on the guardians data, contact number, and less obvious details.
    The value of "qa_pairs" should be a list containing exactly {count} unique JSON objects.
    Each object must have two keys:
    1. "question": A question phrased in the SECOND PERSON, as if you are speaking directly to the student (e.g., "What is YOUR student ID?"). Focus on less obvious or more specific details from the profile.
    2. "answer": The precise, factual answer to that question, taken directly from the text.
    """
    response_str = llm.execute(system_prompt, user_prompt)
    print("   ✅ AI response received.")
    
    # Step 3: Save the final JSON
    print(f"3. Saving the output to '{OUTPUT_FILENAME}'...")
    try:
        qa_json = json.loads(response_str)
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            json.dump(qa_json, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Successfully saved the Q&A pairs.")
        print("\n--- FILE CONTENT ---")
        print(json.dumps(qa_json, indent=2))
        print("--------------------")
    except json.JSONDecodeError:
        print(f"❌ Failed to decode JSON from the AI. The raw response was:\n{response_str}")
    
    print("\n🎉 Process Complete.")

# ==============================
# 5. Main Execution Block
# ==============================
if __name__ == "__main__":
    config = load_config(MODE)
    
    if config:
        # Initialize the LLM service based on the chosen mode
        llm_service = LLMService(config, MODE)

        # Run the generator
        generate_and_save(STUDENT_ID_TO_TEST, NUMBER_OF_QUESTIONS, llm_service)