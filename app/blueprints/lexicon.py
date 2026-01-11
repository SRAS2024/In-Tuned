# app/blueprints/lexicon.py
"""
Lexicon Blueprint

Handles lexicon management:
- List lexicon files
- Upload lexicon files
- Delete lexicon files
- External lexicon lookup and expansion
"""

from __future__ import annotations

from flask import Blueprint, request, g, current_app
from werkzeug.utils import secure_filename

from app.db.repositories.lexicon_repository import LexiconRepository
from app.db.repositories.audit_repository import AuditRepository
from app.utils.responses import api_response, api_error
from app.utils.validation import ValidationSchema, text_field, boolean_field, FieldValidator
from app.utils.security import require_admin, get_client_ip, sanitize_filename
from app.utils.errors import ValidationError, NotFoundError
from app.services.lexicon_service import (
    lookup_word_external,
    expand_lexicon,
    get_lexicon_stats,
    add_word_to_lexicon,
    add_custom_word,
)

lexicon_bp = Blueprint("lexicon", __name__)


# Validation schemas
LOOKUP_SCHEMA = ValidationSchema(
    fields=[
        text_field("word", max_length=100),
        FieldValidator(
            name="language",
            field_type=str,
            required=False,
            allowed_values={"en", "es", "pt"},
            default="en",
        ),
    ]
)

EXPAND_SCHEMA = ValidationSchema(
    fields=[
        FieldValidator(
            name="languages",
            field_type=list,
            required=False,
            default=None,
        ),
        boolean_field("include_slang", required=False, default=True),
        boolean_field("include_vocabulary", required=False, default=True),
        boolean_field("apply_immediately", required=False, default=True),
    ]
)

ADD_WORD_SCHEMA = ValidationSchema(
    fields=[
        text_field("word", max_length=100),
        FieldValidator(
            name="language",
            field_type=str,
            required=False,
            allowed_values={"en", "es", "pt"},
            default="en",
        ),
        boolean_field("include_slang", required=False, default=True),
    ]
)

ADD_CUSTOM_SCHEMA = ValidationSchema(
    fields=[
        text_field("word", max_length=100),
        FieldValidator(
            name="language",
            field_type=str,
            required=False,
            allowed_values={"en", "es", "pt"},
            default="en",
        ),
        FieldValidator(
            name="emotions",
            field_type=dict,
            required=True,
        ),
    ]
)


# Allowed file extensions for lexicon uploads
ALLOWED_EXTENSIONS = {"json", "csv", "txt", "pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@lexicon_bp.route("", methods=["GET"])
@require_admin
def list_lexicons():
    """List all uploaded lexicon files."""
    lexicon_repo = LexiconRepository()

    files = lexicon_repo.get_all_files()

    return api_response(data={"files": files})


@lexicon_bp.route("/upload", methods=["POST"])
@require_admin
def upload_lexicon():
    """
    Upload a new dictionary file for a language.

    Expected multipart form data:
        - language: "en", "es", or "pt"
        - file: the uploaded file
    """
    lexicon_repo = LexiconRepository()
    audit_repo = AuditRepository()

    # Validate language
    language = request.form.get("language", "").strip().lower()
    if language not in {"en", "es", "pt"}:
        raise ValidationError(
            message="language must be one of 'en', 'es', 'pt'",
            field="language",
        )

    # Validate file
    uploaded = request.files.get("file")
    if not uploaded:
        raise ValidationError(message="file is required", field="file")

    if not uploaded.filename:
        raise ValidationError(message="File must have a name", field="file")

    if not allowed_file(uploaded.filename):
        raise ValidationError(
            message=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
            field="file",
        )

    # Check file size
    uploaded.seek(0, 2)  # Seek to end
    size = uploaded.tell()
    uploaded.seek(0)  # Seek back to start

    if size > MAX_FILE_SIZE:
        raise ValidationError(
            message=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
            field="file",
        )

    filename = secure_filename(uploaded.filename)
    content_type = uploaded.mimetype or "application/octet-stream"
    data_bytes = uploaded.read()

    result = lexicon_repo.upload_file(
        language=language,
        filename=filename,
        content_type=content_type,
        data=data_bytes,
    )

    # Audit log
    audit_repo.log_action(
        actor_id=None,
        actor_type="admin",
        action="upload",
        resource_type="lexicon_file",
        resource_id=str(result["id"]),
        after_state={
            "filename": filename,
            "language": language,
            "size": len(data_bytes),
        },
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(data={"file": result}, status_code=201)


@lexicon_bp.route("/<int:file_id>", methods=["DELETE"])
@require_admin
def delete_lexicon(file_id: int):
    """Delete a lexicon file."""
    lexicon_repo = LexiconRepository()
    audit_repo = AuditRepository()

    # Get file info before deletion
    file_info = lexicon_repo.find_by_id(file_id)

    success = lexicon_repo.delete_file(file_id)

    if not success:
        raise NotFoundError("Lexicon file not found")

    # Audit log
    audit_repo.log_action(
        actor_id=None,
        actor_type="admin",
        action="delete",
        resource_type="lexicon_file",
        resource_id=str(file_id),
        before_state=file_info,
        ip_address=get_client_ip(),
        request_id=getattr(g, "request_id", None),
    )

    return api_response(message="Lexicon file deleted")


@lexicon_bp.route("/stats", methods=["GET"])
@require_admin
def lexicon_stats():
    """Get statistics about the current emotion lexicon."""
    stats = get_lexicon_stats()

    return api_response(data={"stats": stats})


@lexicon_bp.route("/lookup", methods=["POST"])
@require_admin
def lookup_word():
    """
    Look up a single word from external dictionary sources.

    Returns definitions, examples, and extracted emotion weights.
    """
    data = request.get_json(silent=True) or {}
    validated = LOOKUP_SCHEMA.validate(data)

    word = validated["word"].lower()
    language = validated.get("language", "en")

    try:
        result = lookup_word_external(word, language)
        return api_response(data={"result": result})

    except Exception as e:
        current_app.logger.error(
            f"Lookup failed: {str(e)}",
            extra={"request_id": getattr(g, "request_id", "unknown")},
        )
        return api_error(
            message=f"Lookup failed: {str(e)}",
            code="LOOKUP_ERROR",
            status_code=500,
        )


@lexicon_bp.route("/expand", methods=["POST"])
@require_admin
def expand_lexicon_endpoint():
    """
    Expand the emotion lexicon by fetching words from external sources.

    This fetches definitions from:
        - Urban Dictionary (English slang)
        - Free Dictionary API (English, Spanish, Portuguese)

    And extracts emotion weights from definitions to expand the lexicon.

    Note: This operation can take several minutes due to API rate limiting.
    """
    data = request.get_json(silent=True) or {}
    validated = EXPAND_SCHEMA.validate(data)

    languages = validated.get("languages") or ["en", "es", "pt"]
    include_slang = validated.get("include_slang", True)
    include_vocabulary = validated.get("include_vocabulary", True)
    apply_immediately = validated.get("apply_immediately", True)

    # Validate languages
    valid_langs = {"en", "es", "pt"}
    languages = [l for l in languages if l in valid_langs]
    if not languages:
        raise ValidationError(
            message="At least one valid language is required",
            field="languages",
        )

    try:
        result = expand_lexicon(
            languages=languages,
            include_slang=include_slang,
            include_vocabulary=include_vocabulary,
            apply_immediately=apply_immediately,
        )

        # Audit log
        audit_repo = AuditRepository()
        audit_repo.log_action(
            actor_id=None,
            actor_type="admin",
            action="expand_lexicon",
            resource_type="lexicon",
            ip_address=get_client_ip(),
            request_id=getattr(g, "request_id", None),
            metadata=result,
        )

        return api_response(data=result)

    except Exception as e:
        current_app.logger.error(
            f"Expansion failed: {str(e)}",
            extra={"request_id": getattr(g, "request_id", "unknown")},
        )
        return api_error(
            message=f"Expansion failed: {str(e)}",
            code="EXPANSION_ERROR",
            status_code=500,
        )


@lexicon_bp.route("/add-word", methods=["POST"])
@require_admin
def add_word():
    """
    Add a single word to the lexicon by fetching from external sources.

    Returns the extracted emotion weights and adds to the active lexicon.
    """
    data = request.get_json(silent=True) or {}
    validated = ADD_WORD_SCHEMA.validate(data)

    word = validated["word"].lower()
    language = validated.get("language", "en")
    include_slang = validated.get("include_slang", language == "en")

    try:
        result = add_word_to_lexicon(word, language, include_slang)

        if not result:
            return api_error(
                message="No emotion associations found for this word",
                code="NO_EMOTIONS_FOUND",
                status_code=404,
                details={"word": word, "language": language},
            )

        # Audit log
        audit_repo = AuditRepository()
        audit_repo.log_action(
            actor_id=None,
            actor_type="admin",
            action="add_word",
            resource_type="lexicon",
            ip_address=get_client_ip(),
            request_id=getattr(g, "request_id", None),
            metadata=result,
        )

        return api_response(data=result)

    except Exception as e:
        current_app.logger.error(
            f"Failed to add word: {str(e)}",
            extra={"request_id": getattr(g, "request_id", "unknown")},
        )
        return api_error(
            message=f"Failed to add word: {str(e)}",
            code="ADD_WORD_ERROR",
            status_code=500,
        )


@lexicon_bp.route("/add-custom", methods=["POST"])
@require_admin
def add_custom():
    """
    Add a word with custom emotion weights (no external lookup).

    Example:
        {
            "word": "yeet",
            "language": "en",
            "emotions": {"joy": 1.5, "surprise": 2.0}
        }
    """
    data = request.get_json(silent=True) or {}
    validated = ADD_CUSTOM_SCHEMA.validate(data)

    word = validated["word"].lower()
    language = validated.get("language", "en")
    emotions = validated["emotions"]

    try:
        result = add_custom_word(word, language, emotions)

        # Audit log
        audit_repo = AuditRepository()
        audit_repo.log_action(
            actor_id=None,
            actor_type="admin",
            action="add_custom_word",
            resource_type="lexicon",
            ip_address=get_client_ip(),
            request_id=getattr(g, "request_id", None),
            metadata=result,
        )

        return api_response(data=result)

    except ValueError as e:
        raise ValidationError(message=str(e))

    except Exception as e:
        current_app.logger.error(
            f"Failed to add custom word: {str(e)}",
            extra={"request_id": getattr(g, "request_id", "unknown")},
        )
        return api_error(
            message=f"Failed to add custom word: {str(e)}",
            code="ADD_CUSTOM_ERROR",
            status_code=500,
        )
