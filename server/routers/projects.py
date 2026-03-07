from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import os
import datetime

router = APIRouter()

WORKSPACE = Path("workspace/projects")

class ProjectSummary(BaseModel):
    slug: str
    title: str
    created_at: str
    has_video: bool
    video_url: Optional[str] = None

@router.get("/projects", response_model=List[ProjectSummary])
async def list_projects():
    """過去のプロジェクト一覧を取得する"""
    if not WORKSPACE.exists():
        return []

    projects = []
    for d in WORKSPACE.iterdir():
        if d.is_dir():
            script_path = d / "script.json"
            if not script_path.exists():
                continue
            
            try:
                with open(script_path, "r", encoding="utf-8") as f:
                    script_data = json.load(f)
                
                title = script_data.get("title", d.name)
                
                # Check for output video
                video_path = d / "outputs" / "final.mp4"
                has_video = video_path.exists()
                video_url = f"/outputs/{d.name}/outputs/final.mp4" if has_video else None
                
                # Get creation/modification time
                mtime = os.path.getmtime(script_path)
                created_at = datetime.datetime.fromtimestamp(mtime).isoformat()
                
                projects.append(ProjectSummary(
                    slug=d.name,
                    title=title,
                    created_at=created_at,
                    has_video=has_video,
                    video_url=video_url
                ))
            except Exception as e:
                print(f"Error reading project {d.name}: {e}")
                continue

    # Sort by created_at descending (newest first)
    projects.sort(key=lambda x: x.created_at, reverse=True)
    return projects

@router.get("/projects/{slug}")
async def get_project(slug: str):
    """特定のプロジェクトの台本データ等を返す"""
    project_dir = WORKSPACE / slug
    script_path = project_dir / "script.json"
    
    if not project_dir.exists() or not script_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
        
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            script_data = json.load(f)
            
        video_path = project_dir / "outputs" / "final.mp4"
        if video_path.exists():
            script_data["video_url"] = f"/outputs/{slug}/outputs/final.mp4"
            
        return script_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read project: {str(e)}")
