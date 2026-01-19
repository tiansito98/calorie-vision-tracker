"""
Claude Vision Service
=====================
Handles food image analysis using Claude's vision capabilities.
"""

import anthropic
import base64
import json
import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FoodAnalysisResult:
    """Structured result from food image analysis."""
    success: bool
    food_items: list
    total_calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
    confidence: float
    description: str
    notes: str
    raw_response: dict
    error: Optional[str] = None


FOOD_ANALYSIS_PROMPT = """Analyze this food image and provide nutritional estimates.

IMPORTANT GUIDELINES:
1. Identify all visible food items and beverages
2. Estimate portion sizes based on visual cues (plate size, utensils, hands, standard dishware)
3. Provide calorie and macro estimates based on typical nutritional data
4. Be conservative with estimates when uncertain - better to underestimate slightly
5. Consider that this may be a home-cooked meal with standard ingredients
6. If the image is unclear or not food, indicate low confidence

Please respond in the following JSON format ONLY (no other text, no markdown):
{
    "food_items": [
        {
            "name": "Item name",
            "portion": "Estimated portion (e.g., '1 cup', '200g', '1 medium')",
            "calories": 000
        }
    ],
    "total_calories": 000,
    "macros": {
        "protein_g": 00.0,
        "carbs_g": 00.0,
        "fat_g": 00.0,
        "fiber_g": 00.0,
        "sugar_g": 00.0
    },
    "confidence": 0.0,
    "description": "Brief description of the meal",
    "notes": "Any relevant notes about the estimation"
}

CONFIDENCE SCORING GUIDE:
- 0.85-1.0: Clear image, common recognizable foods, visible portion indicators
- 0.70-0.85: Good image quality, some estimation required for portions
- 0.50-0.70: Unclear portions, mixed dishes, or unfamiliar foods
- Below 0.50: Significant uncertainty, blurry image, or partially visible food

RESPOND WITH ONLY THE JSON - NO MARKDOWN BACKTICKS OR OTHER TEXT."""


class ClaudeVisionService:
    """Service for analyzing food images using Claude's vision API."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def _encode_image(self, image_data: bytes) -> str:
        """Encode image bytes to base64."""
        return base64.standard_b64encode(image_data).decode("utf-8")
    
    def _get_media_type(self, filename: str) -> str:
        """Determine media type from filename."""
        ext = filename.lower().split(".")[-1]
        media_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }
        return media_types.get(ext, "image/jpeg")
    
    def _parse_response(self, response_text: str) -> Tuple[bool, dict]:
        """Parse the JSON response from Claude."""
        try:
            # Clean the response - remove any markdown formatting
            cleaned = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned.startswith("```"):
                # Find the end of the opening fence
                first_newline = cleaned.find("\n")
                if first_newline != -1:
                    cleaned = cleaned[first_newline + 1:]
                # Remove closing fence
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
            
            # Try to find JSON object
            json_match = re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                cleaned = json_match.group()
            
            data = json.loads(cleaned)
            return True, data
        except json.JSONDecodeError as e:
            return False, {"error": f"Failed to parse response: {str(e)}", "raw": response_text}
    
    def analyze_food_image(
        self, 
        image_data: bytes, 
        filename: str = "image.jpg",
        additional_context: str = ""
    ) -> FoodAnalysisResult:
        """
        Analyze a food image and return nutritional estimates.
        
        Args:
            image_data: Raw bytes of the image
            filename: Original filename for media type detection
            additional_context: Optional context (e.g., "This is lunch", "Colombian cuisine")
        
        Returns:
            FoodAnalysisResult with all nutritional data
        """
        try:
            # Encode image
            base64_image = self._encode_image(image_data)
            media_type = self._get_media_type(filename)
            
            # Build prompt with optional context
            prompt = FOOD_ANALYSIS_PROMPT
            if additional_context:
                prompt = f"Context: {additional_context}\n\n{prompt}"
            
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # Extract response text
            response_text = message.content[0].text
            
            # Parse JSON response
            success, parsed = self._parse_response(response_text)
            
            if not success:
                return FoodAnalysisResult(
                    success=False,
                    food_items=[],
                    total_calories=0,
                    protein_g=0,
                    carbs_g=0,
                    fat_g=0,
                    fiber_g=0,
                    sugar_g=0,
                    confidence=0,
                    description="",
                    notes="",
                    raw_response=parsed,
                    error=parsed.get("error", "Unknown parsing error")
                )
            
            # Extract data with defaults
            macros = parsed.get("macros", {})
            
            return FoodAnalysisResult(
                success=True,
                food_items=parsed.get("food_items", []),
                total_calories=int(parsed.get("total_calories", 0)),
                protein_g=float(macros.get("protein_g", 0)),
                carbs_g=float(macros.get("carbs_g", 0)),
                fat_g=float(macros.get("fat_g", 0)),
                fiber_g=float(macros.get("fiber_g", 0)),
                sugar_g=float(macros.get("sugar_g", 0)),
                confidence=float(parsed.get("confidence", 0.5)),
                description=parsed.get("description", ""),
                notes=parsed.get("notes", ""),
                raw_response=parsed
            )
            
        except anthropic.APIError as e:
            return FoodAnalysisResult(
                success=False,
                food_items=[],
                total_calories=0,
                protein_g=0,
                carbs_g=0,
                fat_g=0,
                fiber_g=0,
                sugar_g=0,
                confidence=0,
                description="",
                notes="",
                raw_response={},
                error=f"API Error: {str(e)}"
            )
        except Exception as e:
            return FoodAnalysisResult(
                success=False,
                food_items=[],
                total_calories=0,
                protein_g=0,
                carbs_g=0,
                fat_g=0,
                fiber_g=0,
                sugar_g=0,
                confidence=0,
                description="",
                notes="",
                raw_response={},
                error=f"Unexpected error: {str(e)}"
            )
    
    def analyze_food_url(self, image_url: str, additional_context: str = "") -> FoodAnalysisResult:
        """
        Analyze a food image from URL.
        
        Args:
            image_url: Public URL of the image
            additional_context: Optional context
        
        Returns:
            FoodAnalysisResult with all nutritional data
        """
        try:
            prompt = FOOD_ANALYSIS_PROMPT
            if additional_context:
                prompt = f"Context: {additional_context}\n\n{prompt}"
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": image_url
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            response_text = message.content[0].text
            success, parsed = self._parse_response(response_text)
            
            if not success:
                return FoodAnalysisResult(
                    success=False,
                    food_items=[],
                    total_calories=0,
                    protein_g=0,
                    carbs_g=0,
                    fat_g=0,
                    fiber_g=0,
                    sugar_g=0,
                    confidence=0,
                    description="",
                    notes="",
                    raw_response=parsed,
                    error=parsed.get("error", "Unknown parsing error")
                )
            
            macros = parsed.get("macros", {})
            
            return FoodAnalysisResult(
                success=True,
                food_items=parsed.get("food_items", []),
                total_calories=int(parsed.get("total_calories", 0)),
                protein_g=float(macros.get("protein_g", 0)),
                carbs_g=float(macros.get("carbs_g", 0)),
                fat_g=float(macros.get("fat_g", 0)),
                fiber_g=float(macros.get("fiber_g", 0)),
                sugar_g=float(macros.get("sugar_g", 0)),
                confidence=float(parsed.get("confidence", 0.5)),
                description=parsed.get("description", ""),
                notes=parsed.get("notes", ""),
                raw_response=parsed
            )
            
        except Exception as e:
            return FoodAnalysisResult(
                success=False,
                food_items=[],
                total_calories=0,
                protein_g=0,
                carbs_g=0,
                fat_g=0,
                fiber_g=0,
                sugar_g=0,
                confidence=0,
                description="",
                notes="",
                raw_response={},
                error=f"Error: {str(e)}"
            )


def create_claude_service(api_key: str, model: str = "claude-sonnet-4-20250514") -> ClaudeVisionService:
    """Factory function to create Claude vision service."""
    return ClaudeVisionService(api_key=api_key, model=model)
