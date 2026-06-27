"""
NLLB Translation Service
Dedicated microservice for multilingual translation using NLLB-200
"""

import asyncio
import logging
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NLLB Translation Service", version="1.0.0")

class TranslationRequest(BaseModel):
    text: str
    source_language: str = "en"
    target_language: str
    
class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    success: bool

class NLLBTranslator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        
        # Language mappings for NLLB
        self.language_codes = {
            'en': 'eng_Latn',
            'hi': 'hin_Deva', 
            'bn': 'ben_Beng',
            'ta': 'tam_Taml',
            'te': 'tel_Telu',
            'kn': 'kan_Knda',
            'ml': 'mal_Mlym',
            'mr': 'mar_Deva',
            'gu': 'guj_Gujr',
            'pa': 'pan_Guru',
            'ne': 'npi_Deva',
            'ur': 'urd_Arab'
        }
        # Model is loaded on FastAPI startup (see @app.on_event("startup")),
        # not in __init__, because there is no running event loop at import time.
    
    async def load_model(self):
        """Load NLLB model asynchronously"""
        try:
            logger.info("🔄 Loading NLLB-200 model...")
            model_name = "facebook/nllb-200-distilled-600M"
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            if self.device == "cuda":
                self.model = self.model.to(self.device)
            
            logger.info("✅ NLLB model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load NLLB model: {e}")
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using NLLB"""
        if not self.model or not self.tokenizer:
            raise HTTPException(status_code=503, detail="Translation model not ready")
        
        if source_lang == target_lang:
            return text
        
        try:
            # Get language codes
            src_code = self.language_codes.get(source_lang, 'eng_Latn')
            tgt_code = self.language_codes.get(target_lang, 'eng_Latn')
            
            # Tokenize input
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                max_length=512, 
                truncation=True
            )
            
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate translation
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(tgt_code),
                    max_length=512,
                    num_beams=5,
                    early_stopping=True
                )
            
            # Decode result
            translated_text = self.tokenizer.decode(
                generated_tokens[0], 
                skip_special_tokens=True
            )
            
            logger.info(f"✅ Translated: {source_lang} -> {target_lang}")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

# Initialize translator
translator = NLLBTranslator()


@app.on_event("startup")
async def load_model_on_startup():
    """Load the NLLB model in the background once the event loop is running."""
    asyncio.create_task(translator.load_model())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_ready = translator.model is not None and translator.tokenizer is not None
    return {
        "status": "healthy" if model_ready else "loading",
        "model_ready": model_ready,
        "device": translator.device,
        "supported_languages": list(translator.language_codes.keys())
    }

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Translate text between supported languages"""
    try:
        translated_text = await translator.translate(
            request.text,
            request.source_language,
            request.target_language
        )
        
        return TranslationResponse(
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "supported_languages": translator.language_codes,
        "total_languages": len(translator.language_codes)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
