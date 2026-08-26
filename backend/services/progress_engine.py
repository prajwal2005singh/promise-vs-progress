"""
progress_engine.py — Promise vs Progress

Converts verified construction observations into a project-level physical
progress estimate.

Current prototype assumptions:
    - All projects are treated as road-construction projects.
    - Generic road-stage weights are used instead of project-specific WBS/BOQ.
    - Evidence does NOT directly modify Project.progress_percent.
    - Progress is recalculated dynamically from verified observations.
    - Repeated observations of the same stage do not stack together.
    - Schedule progress is calculated separately from physical progress.
    - Schedule status is ON_TRACK / AHEAD / BEHIND.
    - No verified observations means physical progress is returned as 0%,
      with status NO_VERIFIED_OBSERVATIONS rather than pretending the project
      is definitively 0% complete.

Later, project-specific BOQ/WBS weights can replace ROAD_STAGE_WEIGHTS.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable
from zoneinfo import ZoneInfo


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIDENCE_THRESHOLD = float(
    os.getenv("PVP_PROGRESS_CONFIDENCE_THRESHOLD", "0.75")
)

PROJECT_TIMEZONE_NAME = os.getenv(
    "PVP_PROJECT_TIMEZONE",
    "Asia/Kolkata",
)

try:
    PROJECT_TIMEZONE = ZoneInfo(PROJECT_TIMEZONE_NAME)
except Exception:
    PROJECT_TIMEZONE = ZoneInfo("Asia/Kolkata")


# Generic road-construction weights.
#
# These are NOT BOQ-derived weights.
# They are prototype assumptions used for all current projects.
ROAD_STAGE_WEIGHTS = {
    "EARTHWORK": 0.20,
    "SUBGRADE": 0.15,
    "DRAINAGE": 0.10,
    "GSB": 0.15,
    "WMM": 0.15,
    "DBM": 0.10,
    "BC": 0.10,
    "MARKING": 0.05,
}


DEFAULT_STAGE_ORDER = [
    "EARTHWORK",
    "SUBGRADE",
    "DRAINAGE",
    "GSB",
    "WMM",
    "DBM",
    "BC",
    "MARKING",
    "COMPLETED",
]


STAGE_COMPLETION_FACTORS = {
    "NOT_STARTED": 0.0,
    "EARLY": 0.25,
    "PARTIAL": 0.50,
    "MOSTLY_COMPLETE": 0.85,
    "COMPLETE": 1.0,
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class VerifiedObservation:
    """
    Normalized observation consumed by the Progress Engine.
    """

    observation_id: int
    captured_at: datetime
    stage: str
    stage_completion: str
    confidence: float
    context_status: str
    evidence_status: str = "APPROVED"


@dataclass
class ScheduleInfo:
    """
    Project schedule information.

    planned_start:
        Project's promised start date.

    planned_completion:
        Project's promised completion date.

    as_of:
        Timestamp at which schedule progress is evaluated.
    """

    planned_start: datetime | None = None
    planned_completion: datetime | None = None
    as_of: datetime | None = None


@dataclass
class ProgressResult:
    status: str
    project_progress_percent: float
    physical_progress_percent: float
    schedule_progress_percent: float | None
    schedule_status: str | None

    calculation_basis: str

    verified_observation_count: int
    contributing_observation_ids: list[int]

    stage_progress: dict[str, float]

    warnings: list[str]


# ---------------------------------------------------------------------------
# Datetime helpers
# ---------------------------------------------------------------------------

def _as_utc_naive(dt: datetime | None) -> datetime | None:
    """
    Normalize a datetime into naive UTC.

    Rules:
        - timezone-aware datetime:
              convert to UTC, then remove tzinfo.
        - timezone-naive datetime:
              interpret it as PROJECT_TIMEZONE, convert to UTC,
              then remove tzinfo.

    This allows arithmetic between DB dates (often naive) and
    server-generated timestamps (often aware) without Python raising:

        TypeError: can't subtract offset-naive and offset-aware datetimes
    """

    if dt is None:
        return None

    if dt.tzinfo is None:
        localized = dt.replace(tzinfo=PROJECT_TIMEZONE)
    else:
        localized = dt.astimezone(timezone.utc)

    return localized.astimezone(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Stage helpers
# ---------------------------------------------------------------------------

def _normalize_stage(value: str | None) -> str | None:
    if not value:
        return None

    stage = value.strip().upper()

    if stage in DEFAULT_STAGE_ORDER:
        return stage

    return None


def _normalize_completion(value: str | None) -> str:
    if not value:
        return "NOT_STARTED"

    completion = value.strip().upper()

    if completion in STAGE_COMPLETION_FACTORS:
        return completion

    return "NOT_STARTED"


# ---------------------------------------------------------------------------
# Observation validation
# ---------------------------------------------------------------------------

def _is_verified_observation(
    observation: VerifiedObservation,
    confidence_threshold: float,
) -> bool:
    """
    Decide whether an observation is allowed to influence project progress.
    """

    return (
        observation.evidence_status == "APPROVED"
        and observation.context_status
        in {
            "VERIFIED",
            "PROVISIONALLY_VERIFIED",
        }
        and observation.confidence >= confidence_threshold
        and _normalize_stage(observation.stage) is not None
    )


# ---------------------------------------------------------------------------
# Schedule helpers
# ---------------------------------------------------------------------------

def _schedule_elapsed_fraction(
    schedule: ScheduleInfo,
) -> float | None:
    """
    Calculate fraction of planned project duration elapsed.

    Returns:
        0.0 → project hasn't started
        1.0 → schedule has reached/passed planned completion
        None → invalid/incomplete schedule
    """

    if not (
        schedule.planned_start
        and schedule.planned_completion
        and schedule.as_of
    ):
        return None

    planned_start = _as_utc_naive(
        schedule.planned_start
    )

    planned_completion = _as_utc_naive(
        schedule.planned_completion
    )

    as_of = _as_utc_naive(
        schedule.as_of
    )

    if (
        planned_start is None
        or planned_completion is None
        or as_of is None
    ):
        return None

    total_seconds = (
        planned_completion - planned_start
    ).total_seconds()

    if total_seconds <= 0:
        return None

    elapsed_seconds = (
        as_of - planned_start
    ).total_seconds()

    return max(
        0.0,
        min(
            1.0,
            elapsed_seconds / total_seconds,
        ),
    )


def _schedule_status(
    physical_progress: float,
    schedule_progress: float,
) -> str:
    """
    Compare physical progress with elapsed planned schedule.

    ±5 percentage points is treated as normal variation.
    """

    difference = (
        physical_progress
        - schedule_progress
    )

    if difference > 5.0:
        return "AHEAD"

    if difference < -5.0:
        return "BEHIND"

    return "ON_TRACK"


# ---------------------------------------------------------------------------
# Observation normalization
# ---------------------------------------------------------------------------

def observations_from_models(
    observations: Iterable[Any],
) -> list[VerifiedObservation]:
    """
    Convert SQLAlchemy Observation objects into Progress Engine inputs.

    Expected Observation fields:

        id
        captured_at
        fine_stage
        stage_completion
        vision_confidence
        context_status

    Evidence status is read through:

        observation.evidence.status
    """

    result: list[VerifiedObservation] = []

    for observation in observations:

        evidence = getattr(
            observation,
            "evidence",
            None,
        )

        evidence_status = (
            getattr(
                evidence,
                "status",
                None,
            )
            if evidence is not None
            else "APPROVED"
        )

        stage = (
            getattr(
                observation,
                "fine_stage",
                None,
            )
            or getattr(
                observation,
                "stage",
                None,
            )
        )

        confidence = float(
            getattr(
                observation,
                "vision_confidence",
                None,
            )
            or 0.0
        )

        context_status = (
            getattr(
                observation,
                "context_status",
                None,
            )
            or "REVIEW"
        )

        captured_at = getattr(
            observation,
            "captured_at",
            None,
        )

        if captured_at is None:
            continue

        result.append(
            VerifiedObservation(
                observation_id=int(
                    observation.id
                ),
                captured_at=captured_at,
                stage=stage or "",
                stage_completion=(
                    getattr(
                        observation,
                        "stage_completion",
                        None,
                    )
                    or "NOT_STARTED"
                ),
                confidence=confidence,
                context_status=context_status,
                evidence_status=(
                    evidence_status
                    or "APPROVED"
                ),
            )
        )

    return result


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class ProgressEngine:

    def __init__(
        self,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ):
        self.confidence_threshold = (
            confidence_threshold
        )

    def calculate(
        self,
        observations: Iterable[VerifiedObservation],
        schedule: ScheduleInfo | None = None,
    ) -> ProgressResult:

        warnings: list[str] = []

        normalized_observations = list(
            observations
        )

        # ---------------------------------------------------------------
        # 1. Filter observations
        # ---------------------------------------------------------------

        verified = [
            observation
            for observation in normalized_observations
            if _is_verified_observation(
                observation,
                self.confidence_threshold,
            )
        ]

        # ---------------------------------------------------------------
        # 2. Schedule calculation
        #
        # Schedule is independent of physical observations.
        # Therefore we can still return schedule progress even if
        # there is no evidence.
        # ---------------------------------------------------------------

        schedule_progress = None
        schedule_status = None

        if schedule is not None:

            elapsed_fraction = (
                _schedule_elapsed_fraction(
                    schedule
                )
            )

            if elapsed_fraction is not None:

                schedule_progress = (
                    elapsed_fraction * 100.0
                )

                # With no verified physical observations,
                # physical progress is currently 0%.
                comparison_physical_progress = (
                    0.0
                    if not verified
                    else None
                )

                if (
                    comparison_physical_progress
                    is not None
                ):
                    schedule_status = (
                        _schedule_status(
                            comparison_physical_progress,
                            schedule_progress,
                        )
                    )

            else:

                warnings.append(
                    "Schedule dates were supplied but "
                    "could not produce a valid elapsed "
                    "schedule fraction."
                )

        # ---------------------------------------------------------------
        # 3. No verified observations
        # ---------------------------------------------------------------

        if not verified:

            warnings.append(
                "No verified observations are available. "
                "Physical progress is currently 0%."
            )

            return ProgressResult(
                status="NO_VERIFIED_OBSERVATIONS",

                project_progress_percent=0.0,

                physical_progress_percent=0.0,

                schedule_progress_percent=(
                    round(
                        schedule_progress,
                        2,
                    )
                    if schedule_progress is not None
                    else None
                ),

                schedule_status=schedule_status,

                calculation_basis=(
                    "GENERIC_ROAD_STAGE_WEIGHTS"
                ),

                verified_observation_count=0,

                contributing_observation_ids=[],

                stage_progress={
                    stage: 0.0
                    for stage in ROAD_STAGE_WEIGHTS
                },

                warnings=warnings,
            )

        # ---------------------------------------------------------------
        # 4. Sort verified observations chronologically
        # ---------------------------------------------------------------

        verified.sort(
            key=lambda observation:
                _as_utc_naive(
                    observation.captured_at
                )
                or datetime.min
        )

        # ---------------------------------------------------------------
        # 5. Build temporal stage history
        #
        # If the same stage is observed repeatedly:
        #
        #   WMM PARTIAL
        #   WMM PARTIAL
        #   WMM MOSTLY_COMPLETE
        #
        # we don't add all observations together.
        #
        # We keep the strongest verified completion state.
        # ---------------------------------------------------------------

        stage_history: dict[str, float] = {}

        stage_observation_ids: dict[
            str,
            list[int],
        ] = {}

        for observation in verified:

            stage = _normalize_stage(
                observation.stage
            )

            if stage is None:
                continue

            completion = _normalize_completion(
                observation.stage_completion
            )

            factor = (
                STAGE_COMPLETION_FACTORS[
                    completion
                ]
            )

            previous = stage_history.get(
                stage,
                0.0,
            )

            if factor > previous:

                stage_history[stage] = factor

                stage_observation_ids[
                    stage
                ] = [
                    observation.observation_id
                ]

        # ---------------------------------------------------------------
        # 6. Calculate weighted physical progress
        # ---------------------------------------------------------------

        stage_progress_percent: dict[
            str,
            float,
        ] = {}

        weighted_progress = 0.0

        contributing_ids: list[int] = []

        for (
            stage_code,
            weight,
        ) in ROAD_STAGE_WEIGHTS.items():

            completion_factor = (
                stage_history.get(
                    stage_code,
                    0.0,
                )
            )

            stage_percent = (
                completion_factor * 100.0
            )

            stage_progress_percent[
                stage_code
            ] = round(
                stage_percent,
                2,
            )

            weighted_progress += (
                weight
                * completion_factor
            )

            contributing_ids.extend(
                stage_observation_ids.get(
                    stage_code,
                    [],
                )
            )

        physical_progress = (
            weighted_progress * 100.0
        )

        # ---------------------------------------------------------------
        # 7. Compare physical progress against schedule
        # ---------------------------------------------------------------

        if schedule_progress is not None:

            schedule_status = (
                _schedule_status(
                    physical_progress,
                    schedule_progress,
                )
            )

        # ---------------------------------------------------------------
        # 8. Return complete result
        # ---------------------------------------------------------------

        return ProgressResult(
            status="CALCULATED",

            project_progress_percent=round(
                physical_progress,
                2,
            ),

            physical_progress_percent=round(
                physical_progress,
                2,
            ),

            schedule_progress_percent=(
                round(
                    schedule_progress,
                    2,
                )
                if schedule_progress is not None
                else None
            ),

            schedule_status=schedule_status,

            calculation_basis=(
                "GENERIC_ROAD_STAGE_WEIGHTS"
            ),

            verified_observation_count=len(
                verified
            ),

            contributing_observation_ids=sorted(
                set(contributing_ids)
            ),

            stage_progress=stage_progress_percent,

            warnings=warnings,
        )


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def calculate_project_progress(
    observations: Iterable[Any],
    schedule: ScheduleInfo | None = None,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> dict:
    """
    Calculate project progress from SQLAlchemy Observation models.

    Returns a JSON-friendly dictionary.
    """

    normalized = (
        observations_from_models(
            observations
        )
    )

    engine = ProgressEngine(
        confidence_threshold=(
            confidence_threshold
        )
    )

    result = engine.calculate(
        observations=normalized,
        schedule=schedule,
    )

    return asdict(result)
