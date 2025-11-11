"""
Call Statistics API - Aggregated statistics by call_category and call_type
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from middleware.auth import get_current_user
from services.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/call-statistics", tags=["call-statistics"])
logger = logging.getLogger(__name__)


class CallTypeStatistics(BaseModel):
    call_type: str
    total: int
    scheduled: int
    not_scheduled: int
    other_question: int
    success_rate: float
    avg_quality_score: float
    total_duration_seconds: int


class CallCategoryStatistics(BaseModel):
    category: str
    total: int
    avg_quality_score: float
    total_duration_seconds: int


class CallStatisticsResponse(BaseModel):
    total_calls: int
    call_type_breakdown: List[CallTypeStatistics]
    call_category_breakdown: List[CallCategoryStatistics]
    date_range: Dict[str, str]


@router.get("/call-types", response_model=CallStatisticsResponse)
async def get_call_type_statistics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics aggregated by call_type and call_category.
    
    Returns:
    - Total calls count
    - Breakdown by call_type (scheduling, pricing, etc.) with success rates
    - Breakdown by call_category (consult_scheduled, consult_not_scheduled, etc.)
    - Average quality scores per type/category
    """
    try:
        supabase = get_supabase_client()
        current_user_id = current_user.get("user_id")
        
        # Use provided user_id or default to current user
        filter_user_id = user_id if user_id else current_user_id
        
        # Build query
        query = supabase.table("call_records").select(
            "id,call_category,call_type,duration_seconds,created_at,user_id"
        ).eq("user_id", filter_user_id)
        
        # Apply date filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.gte("created_at", start_dt.isoformat())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                # Add one day to include the entire end date
                end_dt = end_dt + timedelta(days=1)
                query = query.lt("created_at", end_dt.isoformat())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Execute query
        result = query.execute()
        call_records = result.data or []
        
        logger.info(f"Found {len(call_records)} call records for statistics")
        
        # Aggregate by call_type
        type_stats = {}
        category_stats = {}
        
        # Also fetch quality scores from call_analyses
        call_ids = [cr["id"] for cr in call_records]
        quality_scores_map = {}
        
        if call_ids:
            analyses_result = supabase.table("call_analyses").select(
                "call_record_id,sales_performance_score"
            ).in_("call_record_id", call_ids).execute()
            
            if analyses_result.data:
                for analysis in analyses_result.data:
                    call_id = analysis.get("call_record_id")
                    score = analysis.get("sales_performance_score")
                    if call_id and score is not None:
                        quality_scores_map[call_id] = score
        
        # Process each call record
        for record in call_records:
            call_type = record.get("call_type") or "unknown"
            call_category = record.get("call_category") or "unknown"
            duration = record.get("duration_seconds") or 0
            call_id = record.get("id")
            quality_score = quality_scores_map.get(call_id)
            
            # Aggregate by call_type
            if call_type not in type_stats:
                type_stats[call_type] = {
                    "total": 0,
                    "scheduled": 0,
                    "not_scheduled": 0,
                    "other_question": 0,
                    "quality_scores": [],
                    "total_duration": 0
                }
            
            type_stats[call_type]["total"] += 1
            type_stats[call_type]["total_duration"] += duration
            
            if call_category == "consult_scheduled":
                type_stats[call_type]["scheduled"] += 1
            elif call_category == "consult_not_scheduled":
                type_stats[call_type]["not_scheduled"] += 1
            else:
                type_stats[call_type]["other_question"] += 1
            
            if quality_score is not None:
                type_stats[call_type]["quality_scores"].append(quality_score)
            
            # Aggregate by call_category
            if call_category not in category_stats:
                category_stats[call_category] = {
                    "total": 0,
                    "quality_scores": [],
                    "total_duration": 0
                }
            
            category_stats[call_category]["total"] += 1
            category_stats[call_category]["total_duration"] += duration
            
            if quality_score is not None:
                category_stats[call_category]["quality_scores"].append(quality_score)
        
        # Convert to response format
        call_type_breakdown = []
        for call_type, stats in type_stats.items():
            success_rate = (stats["scheduled"] / stats["total"] * 100) if stats["total"] > 0 else 0
            avg_quality = (
                sum(stats["quality_scores"]) / len(stats["quality_scores"])
                if stats["quality_scores"] else 0
            )
            
            call_type_breakdown.append(CallTypeStatistics(
                call_type=call_type.replace("_", " ").title() if call_type != "unknown" else "Not Classified",
                total=stats["total"],
                scheduled=stats["scheduled"],
                not_scheduled=stats["not_scheduled"],
                other_question=stats["other_question"],
                success_rate=round(success_rate, 2),
                avg_quality_score=round(avg_quality, 2),
                total_duration_seconds=stats["total_duration"]
            ))
        
        # Sort by total (descending)
        call_type_breakdown.sort(key=lambda x: x.total, reverse=True)
        
        # Convert category stats
        call_category_breakdown = []
        for category, stats in category_stats.items():
            avg_quality = (
                sum(stats["quality_scores"]) / len(stats["quality_scores"])
                if stats["quality_scores"] else 0
            )
            
            call_category_breakdown.append(CallCategoryStatistics(
                category=category.replace("_", " ").title() if category != "unknown" else "Not Classified",
                total=stats["total"],
                avg_quality_score=round(avg_quality, 2),
                total_duration_seconds=stats["total_duration"]
            ))
        
        # Sort by total (descending)
        call_category_breakdown.sort(key=lambda x: x.total, reverse=True)
        
        # Determine date range
        if call_records:
            dates = [datetime.fromisoformat(cr["created_at"].replace('Z', '+00:00')) for cr in call_records]
            min_date = min(dates)
            max_date = max(dates)
            date_range = {
                "start": min_date.isoformat(),
                "end": max_date.isoformat()
            }
        else:
            date_range = {
                "start": start_date or datetime.now().isoformat(),
                "end": end_date or datetime.now().isoformat()
            }
        
        return CallStatisticsResponse(
            total_calls=len(call_records),
            call_type_breakdown=call_type_breakdown,
            call_category_breakdown=call_category_breakdown,
            date_range=date_range
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get call statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get call statistics: {str(e)}"
        )


@router.get("/summary", response_model=Dict[str, Any])
async def get_call_statistics_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    Get a quick summary of call statistics for the current user.
    Returns key metrics without requiring date filters.
    """
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("user_id")
        
        # Get total calls
        total_result = supabase.table("call_records").select("id", count="exact").eq("user_id", user_id).execute()
        total_calls = total_result.count or 0
        
        # Get calls by category
        scheduled_result = supabase.table("call_records").select("id", count="exact").eq("user_id", user_id).eq("call_category", "consult_scheduled").execute()
        not_scheduled_result = supabase.table("call_records").select("id", count="exact").eq("user_id", user_id).eq("call_category", "consult_not_scheduled").execute()
        
        scheduled_count = scheduled_result.count or 0
        not_scheduled_count = not_scheduled_result.count or 0
        
        # Get top call types
        calls_result = supabase.table("call_records").select("call_type").eq("user_id", user_id).not_.is_("call_type", "null").execute()
        
        call_type_counts = {}
        if calls_result.data:
            for record in calls_result.data:
                call_type = record.get("call_type")
                if call_type:
                    call_type_counts[call_type] = call_type_counts.get(call_type, 0) + 1
        
        top_call_types = sorted(call_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_calls": total_calls,
            "scheduled": scheduled_count,
            "not_scheduled": not_scheduled_count,
            "success_rate": round((scheduled_count / total_calls * 100) if total_calls > 0 else 0, 2),
            "top_call_types": [
                {"type": k.replace("_", " ").title(), "count": v}
                for k, v in top_call_types
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get call statistics summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get call statistics summary: {str(e)}"
        )

