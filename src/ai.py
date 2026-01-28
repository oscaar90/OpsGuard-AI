import os
import json
import time
import traceback
from openai import OpenAI
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class AIEngineError(Exception):
    """Custom exception for AI Engine failures."""
    pass

SYSTEM_PROMPT = """
You are OpsGuard-AI, a Senior Security Engineer.
INPUT CONTEXT: Git diff analysis.
RULES: Focus on added lines. Output JSON.
JSON SCHEMA: {"risk_score": int, "verdict": str, "issues": []}
"""

class AIEngine:
    def __init__(self):
        raw_key = os.getenv("OPENROUTER_API_KEY")
        if not raw_key:
            raise AIEngineError("❌ Missing OPENROUTER_API_KEY")

        self.api_key = raw_key.strip().strip('"').strip("'")
        
        extra_headers = {
            "HTTP-Referer": "https://opsguard.local",
            "X-Title": "OpsGuard-TFM"
        }

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            default_headers=extra_headers,
            timeout=60.0
        )
        
        # Modelo Ganador
        self.model = "google/gemini-2.0-flash-001"

    def analyze_diff(self, diff_text: str) -> Dict[str, Any]:
        print(f"🤖 Sending diff to AI ({self.model})...")
        print(f"📦 Payload Size: {len(diff_text)} chars")

        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this diff:\n\n{diff_text}"}
                ],
                temperature=0.2,
                max_tokens=1024,
                response_format={"type": "json_object"} 
            )

            end_time = time.time()
            duration = end_time - start_time
            print(f"\033[96m⏱️  AI Analysis Time: {duration:.2f} seconds\033[0m")

            content = response.choices[0].message.content
            clean_content = content.replace("```json", "").replace("```", "").strip()
            
            # --- PARCHE DE ROBUSTEZ ---
            parsed_data = json.loads(clean_content)
            
            # Si la IA devolvió una lista, cogemos el primer elemento
            if isinstance(parsed_data, list):
                if len(parsed_data) > 0:
                    return parsed_data[0]
                else:
                    return {"risk_score": 0, "verdict": "APPROVE", "issues": []}
            
            # Si ya es un dict, lo devolvemos tal cual
            return parsed_data
            # --------------------------

        except Exception as e:
            print(f"\n❌ EXCEPCIÓN AI:")
            # traceback.print_exc() # Descomentar si quieres ver todo el error
            raise AIEngineError(f"AI Process Failed: {str(e)}")