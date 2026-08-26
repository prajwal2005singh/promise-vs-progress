"""
image_engine.py — Promise vs Progress
--------------------------------------
Image-only road-construction interpretation.

Responsibilities:
  - optional frozen CLIP broad-class routing (if a trained joblib model is configured)
  - Gemini VLM fine-stage interpretation
  - no project-level progress calculation
  - no BOQ/schedule reasoning

Fine stages returned by the VLM:
  EARTHWORK, SUBGRADE, DRAINAGE, GSB, WMM, DBM, BC, MARKING, COMPLETED

The CLIP model is a weak prior only; VLM visual evidence has priority.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()
log = logging.getLogger(__name__)

FINE_STAGES = [
    "EARTHWORK", "SUBGRADE", "DRAINAGE", "GSB", "WMM",
    "DBM", "BC", "MARKING", "COMPLETED"
]

BROAD_TO_FINE = {
    "SITE_PREP": ["EARTHWORK", "SUBGRADE", "DRAINAGE"],
    "GRANULAR_BASE": ["GSB", "WMM"],
    "BITUMINOUS": ["DBM", "BC"],
    "FINISHING": ["MARKING", "COMPLETED"],
    "NOT_ROAD": [],
}

class VLMAnalysis(BaseModel):
    is_road_construction: bool
    stage: str | None = Field(default=None)
    stage_completion: str
    visible_components: list[str] = Field(default_factory=list)
    visible_activities: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str

class ImageEngine:
    def __init__(self):
        self.gemini_model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.5-flash-lite")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.clip_model_path = os.getenv("PVP_CLIP_MODEL_PATH")
        self.clip = None
        self.clip_error = None
        self._try_load_clip()

    def _try_load_clip(self):
        if not self.clip_model_path:
            self.clip_error = "PVP_CLIP_MODEL_PATH not configured; using VLM-only mode."
            return

        model_path = Path(self.clip_model_path)
        if not model_path.exists():
            self.clip_error = f"CLIP classifier not found: {model_path}"
            return

        try:
            import joblib
            import numpy as np
            import torch
            import open_clip
            from PIL import Image

            self._torch = torch
            self._np = np
            self._Image = Image
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._clip_model, _, self._clip_preprocess = open_clip.create_model_and_transforms(
                "ViT-B-32", pretrained="openai"
            )
            self._clip_model.eval().to(self._device)
            package = joblib.load(model_path)
            self.clip_classifier = package["model"]
            self.clip_classes = package["classes"]
            self.clip = True
            log.info("Image Engine CLIP router loaded from %s", model_path)
        except Exception as exc:
            self.clip_error = str(exc)
            self.clip = None
            log.warning("CLIP router unavailable; continuing with VLM only: %s", exc)

    def _clip_predict(self, image_path: str) -> dict:
        if not self.clip:
            return {
                "enabled": False,
                "predicted_class": None,
                "confidence": None,
                "probabilities": {},
                "reason": self.clip_error,
            }

        image = self._Image.open(image_path).convert("RGB")
        tensor = self._clip_preprocess(image).unsqueeze(0).to(self._device)
        with self._torch.no_grad():
            embedding = self._clip_model.encode_image(tensor)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        probs = self.clip_classifier.predict_proba(embedding.cpu().numpy())[0]
        idx = int(probs.argmax())
        return {
            "enabled": True,
            "predicted_class": str(self.clip_classes[idx]),
            "confidence": float(probs[idx]),
            "probabilities": {str(c): float(p) for c, p in zip(self.clip_classes, probs)},
            "reason": None,
        }

    def _fallback(self, reason: str) -> dict:
        return {
            "is_road_construction": False,
            "broad_stage": None,
            "stage": None,
            "stage_completion": "UNKNOWN",
            "visible_components": [],
            "visible_activities": [],
            "evidence": [],
            "confidence": None,
            "reason": reason,
            "clip": None,
        }

    def analyze(self, image_path: str) -> dict:
        clip_result = self._clip_predict(image_path)
        broad_hint = clip_result.get("predicted_class")
        fine_hint = BROAD_TO_FINE.get(broad_hint, []) if broad_hint else FINE_STAGES

        if not self.google_api_key:
            return self._fallback("GOOGLE_API_KEY is not configured.") | {"clip": clip_result}

        try:
            from google import genai
            from google.genai import types

            prompt = f"""
You are the road-construction Image Engine for Promise vs Progress.
Analyze ONLY what is visible in this single image. Do not estimate total project percentage.

Scope: Indian road construction.

Valid fine stages:
EARTHWORK, SUBGRADE, DRAINAGE, GSB, WMM, DBM, BC, MARKING, COMPLETED

Definitions:
- EARTHWORK: excavation, cutting/filling, embankment, soil movement.
- SUBGRADE: prepared/graded/compacted soil formation before granular layers.
- DRAINAGE: side drains, culverts, drainage pipes/channels.
- GSB: granular sub-base being spread/graded/compacted.
- WMM: wet mix macadam being spread/graded/compacted.
- DBM: dense bituminous macadam, coarse intermediate asphalt layer.
- BC: final bituminous concrete/wearing course, smoother asphalt.
- MARKING: lane/edge markings, thermoplastic paint, road studs.
- COMPLETED: finished road in normal use, normally with final markings.

Stage completion refers ONLY to the currently visible stage:
NOT_STARTED, EARLY, PARTIAL, MOSTLY_COMPLETE, COMPLETE.

A lightweight CLIP router gave this weak broad hint:
  broad_stage = {broad_hint or 'UNKNOWN'}
  confidence = {clip_result.get('confidence')}
Related fine stages to consider first: {fine_hint}

The CLIP hint can be wrong. Visual evidence has priority.

Return structured JSON with:
is_road_construction, stage, stage_completion, visible_components,
visible_activities, evidence, confidence, reason.

Never invent dimensions, road length, BOQ quantities, schedule status, or total progress percentage.
"""

            mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
            client = genai.Client(api_key=self.google_api_key)
            response = client.models.generate_content(
                model=self.gemini_model,
                contents=[
                    types.Part.from_bytes(data=Path(image_path).read_bytes(), mime_type=mime),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VLMAnalysis,
                    temperature=0.0,
                ),
            )
            analysis = response.parsed

            stage = analysis.stage if analysis.stage in FINE_STAGES else None
            if not analysis.is_road_construction:
                stage = None

            return {
                "is_road_construction": bool(analysis.is_road_construction),
                "broad_stage": broad_hint,
                "stage": stage,
                "stage_completion": analysis.stage_completion,
                "visible_components": analysis.visible_components,
                "visible_activities": analysis.visible_activities,
                "evidence": analysis.evidence,
                "confidence": float(analysis.confidence),
                "reason": analysis.reason,
                "clip": clip_result,
            }
        except Exception as exc:
            log.exception("Image Engine VLM analysis failed")
            return self._fallback(f"Image analysis unavailable: {exc}") | {"clip": clip_result}


image_engine = ImageEngine()
