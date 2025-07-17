import aiohttp
import json
import logging
from config import Config
from typing import Optional

logger = logging.getLogger(__name__)

class DeepseekService:
    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.api_url = Config.DEEPSEEK_API_URL
        
    async def edit_text(self, original_text: str, prompt: str) -> Optional[str]:
        """
        Edit text using Deepseek API
        
        Args:
            original_text: Original text to edit
            prompt: Prompt for editing (template or custom)
            
        Returns:
            Edited text or None if error
        """
        if not self.api_key:
            logger.error("Deepseek API key not configured")
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты - помощник для редактирования текста. Ты получаешь текст и инструкцию по его изменению. Твоя задача - отредактировать текст согласно инструкции, сохранив основную мысль и смысл."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nТекст для редактирования:\n{original_text}"
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        edited_text = result['choices'][0]['message']['content'].strip()
                        logger.info(f"Text edited successfully. Original length: {len(original_text)}, Edited length: {len(edited_text)}")
                        return edited_text
                    else:
                        error_text = await response.text()
                        logger.error(f"Deepseek API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling Deepseek API: {str(e)}")
            return None
    
    async def test_connection(self) -> bool:
        """Test connection to Deepseek API"""
        if not self.api_key:
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": "Привет! Это тестовое сообщение."
                    }
                ],
                "max_tokens": 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error testing Deepseek API connection: {str(e)}")
            return False 