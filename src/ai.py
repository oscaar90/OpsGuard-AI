import os
import json
import time
from openai import OpenAI
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class AIEngineError(Exception):
    """Custom exception for AI Engine failures."""
    pass

# SCHEMA ENFORCEMENT: Definimos la estructura exacta para evitar alucinaciones.
SYSTEM_PROMPT = """
ROLE: You are OpsGuard-AI, a Senior Application Security Engineer audit bot.
TASK: Analyze the provided Git Diff for SECURITY VULNERABILITIES (Secrets, SQLi, XSS, RCE, Bad IAM, PII).

RULES:
1. Ignore style, formatting, or logic bugs. FOCUS ONLY ON SECURITY.
2. If safe, verdict is "APPROVE".
3. If unsafe, verdict is "BLOCK" and you MUST list specific findings.

OUTPUT FORMAT (Strict JSON):
{
    "verdict": "APPROVE" | "BLOCK",
    "risk_score": <integer 0-10>,
    "explanation": "Brief executive summary of the security status.",
    "findings": [
        {
            "file": "path/to/file.ext",
            "line": "approximate line number or code snippet",
            "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
            "issue": "Technical description of the vulnerability"
        }
    ]
}
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
        
        self.model = "google/gemini-2.0-flash-001"

    def analyze_diff(self, diff_text: str) -> Dict[str, Any]:
        print(f"🤖 OpsGuard Brain: Sending diff to {self.model}...")
        print(f"📦 Context Payload: {len(diff_text)} chars")

        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    # Truncate defensivo a 30k chars para evitar errores de contexto
                    {"role": "user", "content": f"Analyze this git diff:\n\n{diff_text[:30000]}"}
                ],
                temperature=0.1, # Determinista
                max_tokens=1024,
                response_format={"type": "json_object"} 
            )

            end_time = time.time()
            duration = end_time - start_time
            print(f"\033[96m⏱️  AI Analysis Time: {duration:.2f} seconds\033[0m")

            content = response.choices[0].message.content
            clean_content = content.replace("```json", "").replace("```", "").strip()
            
            try:
                parsed_data = json.loads(clean_content)
            except json.JSONDecodeError:
                print(f"⚠️ RAW AI RESPONSE (JSON Error): {clean_content}")
                return {
                    "verdict": "BLOCK",
                    "risk_score": 10,
                    "explanation": "AI output parsing failed. Manual review required.",
                    "findings": []
                }
            
            # Normalización de respuesta (Gemini a veces devuelve lista)
            if isinstance(parsed_data, list):
                parsed_data = parsed_data[0] if parsed_data else {}
            
            # Mapeo defensivo de claves
            return {
                "verdict": parsed_data.get("verdict", "BLOCK"),
                "risk_score": parsed_data.get("risk_score", 0),
                "explanation": parsed_data.get("explanation", "No explanation provided."),
                "findings": parsed_data.get("findings", [])
            }

        except Exception as e:
            print(f"\n❌ EXCEPCIÓN AI CRÍTICA: {str(e)}")
            # Fail closed: Si falla el motor, bloqueamos por seguridad
            return {
                "verdict": "BLOCK",
                "risk_score": 10,
                "explanation": f"Internal Engine Error: {str(e)}",
                "findings": []
            }