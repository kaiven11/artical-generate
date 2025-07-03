"""
API routes for prompt template management.
"""

import logging
import json
import io
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..core.database import get_db_connection
from ..models.prompt import PromptType
from ..services.prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prompts", tags=["prompts"])

# Pydantic models for API requests/responses
class PromptTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    type: str = Field(..., description="Template type: translation, optimization, etc.")
    template: str = Field(..., min_length=1)
    variables: Optional[List[str]] = []
    version: str = "1.0"
    language: str = "zh-CN"
    parameters: Optional[Dict[str, Any]] = {}
    priority: int = 0
    test_group: Optional[str] = None

class PromptTemplateUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    template: Optional[str] = None
    variables: Optional[List[str]] = None
    version: Optional[str] = None
    language: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None
    test_group: Optional[str] = None

class PromptTemplateResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    type: str
    template: str
    variables: List[str]
    version: str
    language: str
    success_rate: float
    usage_count: int
    average_quality_score: float
    parameters: Dict[str, Any]
    is_active: bool
    is_default: bool
    priority: int
    test_group: Optional[str]
    created_at: str
    updated_at: str
    last_used_at: Optional[str]
    created_by: str

class PromptTemplateListResponse(BaseModel):
    templates: List[PromptTemplateResponse]
    total: int
    page: int
    page_size: int

class BulkOperationRequest(BaseModel):
    template_ids: List[int]
    operation: str  # activate, deactivate, delete, set_default
    
class ImportRequest(BaseModel):
    templates: List[PromptTemplateCreate]
    overwrite_existing: bool = False


@router.get("/", response_model=PromptTemplateListResponse)
async def list_prompt_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type_filter: Optional[str] = Query(None, alias="type"),
    active_only: bool = Query(False),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc")
):
    """Get list of prompt templates with pagination and filtering."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if type_filter:
            where_conditions.append("type = ?")
            params.append(type_filter)
        
        if active_only:
            where_conditions.append("is_active = 1")
        
        if search:
            where_conditions.append("(name LIKE ? OR display_name LIKE ? OR description LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Build ORDER BY clause
        valid_sort_fields = ["name", "display_name", "type", "created_at", "updated_at", "priority", "usage_count"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "desc"
        
        order_clause = f" ORDER BY {sort_by} {sort_order.upper()}"
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM prompt_templates{where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get paginated results
        offset = (page - 1) * page_size
        query = f"""
            SELECT id, name, display_name, description, type, template, variables, version, language,
                   success_rate, usage_count, average_quality_score, parameters, is_active, is_default,
                   priority, test_group, created_at, updated_at, last_used_at, created_by
            FROM prompt_templates{where_clause}{order_clause}
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, params + [page_size, offset])
        rows = cursor.fetchall()
        
        templates = []
        for row in rows:
            template_dict = dict(row)
            
            # Parse JSON fields
            try:
                # Handle variables field - could be JSON string or Python list string
                variables_str = template_dict['variables'] or '[]'
                if variables_str.startswith('[') and variables_str.endswith(']'):
                    # Try to parse as JSON first
                    try:
                        template_dict['variables'] = json.loads(variables_str)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try to evaluate as Python literal
                        import ast
                        template_dict['variables'] = ast.literal_eval(variables_str)
                else:
                    # If it's a space-separated string, split it
                    if variables_str.strip():
                        template_dict['variables'] = [v.strip() for v in variables_str.split() if v.strip()]
                    else:
                        template_dict['variables'] = []
            except Exception:
                template_dict['variables'] = []

            try:
                template_dict['parameters'] = json.loads(template_dict['parameters'] or '{}')
            except json.JSONDecodeError:
                template_dict['parameters'] = {}
            
            templates.append(PromptTemplateResponse(**template_dict))
        
        conn.close()
        
        return PromptTemplateListResponse(
            templates=templates,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to list prompt templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(template_id: int):
    """Get a specific prompt template by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, display_name, description, type, template, variables, version, language,
                   success_rate, usage_count, average_quality_score, parameters, is_active, is_default,
                   priority, test_group, created_at, updated_at, last_used_at, created_by
            FROM prompt_templates WHERE id = ?
        """, (template_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        template_dict = dict(row)

        # Parse JSON fields
        try:
            # Handle variables field - could be JSON string or Python list string
            variables_str = template_dict['variables'] or '[]'
            if variables_str.startswith('[') and variables_str.endswith(']'):
                # Try to parse as JSON first
                try:
                    template_dict['variables'] = json.loads(variables_str)
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to evaluate as Python literal
                    import ast
                    template_dict['variables'] = ast.literal_eval(variables_str)
            else:
                # If it's a space-separated string, split it
                if variables_str.strip():
                    template_dict['variables'] = [v.strip() for v in variables_str.split() if v.strip()]
                else:
                    template_dict['variables'] = []
        except Exception:
            template_dict['variables'] = []

        try:
            template_dict['parameters'] = json.loads(template_dict['parameters'] or '{}')
        except json.JSONDecodeError:
            template_dict['parameters'] = {}
        
        conn.close()
        
        return PromptTemplateResponse(**template_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PromptTemplateResponse)
async def create_prompt_template(template: PromptTemplateCreate):
    """Create a new prompt template."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if name already exists
        cursor.execute("SELECT id FROM prompt_templates WHERE name = ?", (template.name,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Template name already exists")
        
        # Insert new template
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO prompt_templates (
                name, display_name, description, type, template, variables, version, language,
                parameters, priority, test_group, created_at, updated_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            template.name,
            template.display_name,
            template.description,
            template.type,
            template.template,
            json.dumps(template.variables or []),
            template.version,
            template.language,
            json.dumps(template.parameters or {}),
            template.priority,
            template.test_group,
            now,
            now,
            "user"
        ))
        
        template_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return the created template
        return await get_prompt_template(template_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create prompt template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(template_id: int, template: PromptTemplateUpdate):
    """Update an existing prompt template."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if template exists
        cursor.execute("SELECT id FROM prompt_templates WHERE id = ?", (template_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Prompt template not found")

        # Build update query
        update_fields = []
        params = []

        for field, value in template.dict(exclude_unset=True).items():
            if field in ['variables', 'parameters'] and value is not None:
                value = json.dumps(value)
            update_fields.append(f"{field} = ?")
            params.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Add updated_at
        update_fields.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(template_id)

        query = f"UPDATE prompt_templates SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)

        conn.commit()
        conn.close()

        # Return the updated template
        return await get_prompt_template(template_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update prompt template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def delete_prompt_template(template_id: int):
    """Delete a prompt template."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if template exists
        cursor.execute("SELECT id, is_default FROM prompt_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Prompt template not found")

        # Prevent deletion of default templates
        if row[1]:  # is_default
            raise HTTPException(status_code=400, detail="Cannot delete default template")

        cursor.execute("DELETE FROM prompt_templates WHERE id = ?", (template_id,))
        conn.commit()
        conn.close()

        return {"message": "Template deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete prompt template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", response_model=Dict[str, Any])
async def bulk_operations(request: BulkOperationRequest):
    """Perform bulk operations on prompt templates."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if not request.template_ids:
            raise HTTPException(status_code=400, detail="No template IDs provided")

        placeholders = ",".join("?" * len(request.template_ids))

        if request.operation == "activate":
            cursor.execute(
                f"UPDATE prompt_templates SET is_active = 1, updated_at = ? WHERE id IN ({placeholders})",
                [datetime.now().isoformat()] + request.template_ids
            )
        elif request.operation == "deactivate":
            cursor.execute(
                f"UPDATE prompt_templates SET is_active = 0, updated_at = ? WHERE id IN ({placeholders})",
                [datetime.now().isoformat()] + request.template_ids
            )
        elif request.operation == "delete":
            # Check for default templates
            cursor.execute(
                f"SELECT id FROM prompt_templates WHERE id IN ({placeholders}) AND is_default = 1",
                request.template_ids
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Cannot delete default templates")

            cursor.execute(f"DELETE FROM prompt_templates WHERE id IN ({placeholders})", request.template_ids)
        elif request.operation == "set_default":
            if len(request.template_ids) != 1:
                raise HTTPException(status_code=400, detail="Can only set one template as default")

            # First, unset all defaults for the same type
            cursor.execute("SELECT type FROM prompt_templates WHERE id = ?", (request.template_ids[0],))
            template_type = cursor.fetchone()[0]

            cursor.execute("UPDATE prompt_templates SET is_default = 0 WHERE type = ?", (template_type,))
            cursor.execute(
                "UPDATE prompt_templates SET is_default = 1, updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), request.template_ids[0])
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")

        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()

        return {
            "message": f"Operation '{request.operation}' completed successfully",
            "affected_rows": affected_rows
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform bulk operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_templates(request: ImportRequest):
    """Import prompt templates from JSON data."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        imported_count = 0
        updated_count = 0
        errors = []

        for template_data in request.templates:
            try:
                # Check if template already exists
                cursor.execute("SELECT id FROM prompt_templates WHERE name = ?", (template_data.name,))
                existing = cursor.fetchone()

                if existing and not request.overwrite_existing:
                    errors.append(f"Template '{template_data.name}' already exists")
                    continue

                now = datetime.now().isoformat()

                if existing and request.overwrite_existing:
                    # Update existing template
                    cursor.execute("""
                        UPDATE prompt_templates SET
                            display_name = ?, description = ?, type = ?, template = ?,
                            variables = ?, version = ?, language = ?, parameters = ?,
                            priority = ?, test_group = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        template_data.display_name,
                        template_data.description,
                        template_data.type,
                        template_data.template,
                        json.dumps(template_data.variables or []),
                        template_data.version,
                        template_data.language,
                        json.dumps(template_data.parameters or {}),
                        template_data.priority,
                        template_data.test_group,
                        now,
                        existing[0]
                    ))
                    updated_count += 1
                else:
                    # Insert new template
                    cursor.execute("""
                        INSERT INTO prompt_templates (
                            name, display_name, description, type, template, variables, version, language,
                            parameters, priority, test_group, created_at, updated_at, created_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        template_data.name,
                        template_data.display_name,
                        template_data.description,
                        template_data.type,
                        template_data.template,
                        json.dumps(template_data.variables or []),
                        template_data.version,
                        template_data.language,
                        json.dumps(template_data.parameters or {}),
                        template_data.priority,
                        template_data.test_group,
                        now,
                        now,
                        "import"
                    ))
                    imported_count += 1

            except Exception as e:
                errors.append(f"Failed to import template '{template_data.name}': {str(e)}")

        conn.commit()
        conn.close()

        return {
            "message": "Import completed",
            "imported_count": imported_count,
            "updated_count": updated_count,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Failed to import templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_templates(
    template_ids: Optional[List[int]] = Query(None),
    type_filter: Optional[str] = Query(None, alias="type"),
    format: str = Query("json", regex="^(json|csv)$")
):
    """Export prompt templates to JSON or CSV format."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        where_conditions = []
        params = []

        if template_ids:
            placeholders = ",".join("?" * len(template_ids))
            where_conditions.append(f"id IN ({placeholders})")
            params.extend(template_ids)

        if type_filter:
            where_conditions.append("type = ?")
            params.append(type_filter)

        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        query = f"""
            SELECT id, name, display_name, description, type, template, variables, version, language,
                   success_rate, usage_count, average_quality_score, parameters, is_active, is_default,
                   priority, test_group, created_at, updated_at, last_used_at, created_by
            FROM prompt_templates{where_clause}
            ORDER BY type, name
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        if format == "json":
            templates = []
            for row in rows:
                template_dict = dict(row)
                template_dict['variables'] = json.loads(template_dict['variables'] or '[]')
                template_dict['parameters'] = json.loads(template_dict['parameters'] or '{}')
                templates.append(template_dict)

            output = io.StringIO()
            json.dump(templates, output, indent=2, ensure_ascii=False)
            output.seek(0)

            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=prompt_templates.json"}
            )

        elif format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            if rows:
                writer.writerow(rows[0].keys())

                # Write data
                for row in rows:
                    row_data = []
                    for value in row:
                        if isinstance(value, (dict, list)):
                            row_data.append(json.dumps(value))
                        else:
                            row_data.append(str(value) if value is not None else "")
                    writer.writerow(row_data)

            output.seek(0)

            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=prompt_templates.csv"}
            )

        conn.close()

    except Exception as e:
        logger.error(f"Failed to export templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
