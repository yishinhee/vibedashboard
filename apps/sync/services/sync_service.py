"""
동기화 서비스 — mtime 비교 + 파서 호출 + SyncLog 기록.

agents.md §아키텍처:
- 외부 폴더는 read-only 참조. open(...,'w') / os.remove 등 일체 금지.
- 파싱 실패는 예외 throw 가 아니라 SyncLog.result='failed' + detail 에 사유.
- 파일 누락은 다른 파일 처리에 영향 주지 않는다 (계속 진행).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from django.utils import timezone

from apps.parsers.services import PARSER_REGISTRY
from apps.projects.models import Project
from apps.sync.models import SyncLog


def sync_one_file(project: Project, filename: str) -> str:
    """단일 파일 동기화. SyncLog 1행 기록 후 result 문자열 반환.

    반환: "success" / "failed" / "no_change".
    """
    filepath = Path(project.path) / "docs" / filename

    if not filepath.exists():
        SyncLog.objects.create(
            project=project,
            file_name=filename,
            result=SyncLog.Result.FAILED,
            detail="file not found",
        )
        return SyncLog.Result.FAILED

    file_mtime = timezone.make_aware(
        datetime.fromtimestamp(filepath.stat().st_mtime)
    )
    last_success = (
        SyncLog.objects
        .filter(project=project, file_name=filename, result=SyncLog.Result.SUCCESS)
        .order_by("-synced_at")
        .first()
    )

    if last_success and last_success.file_mtime == file_mtime:
        SyncLog.objects.create(
            project=project,
            file_name=filename,
            file_mtime=file_mtime,
            changed=False,
            result=SyncLog.Result.NO_CHANGE,
            detail="mtime unchanged",
        )
        return SyncLog.Result.NO_CHANGE

    parser_cls = PARSER_REGISTRY.get(filename)
    if parser_cls is None:
        SyncLog.objects.create(
            project=project,
            file_name=filename,
            file_mtime=file_mtime,
            result=SyncLog.Result.FAILED,
            detail="no parser registered",
        )
        return SyncLog.Result.FAILED

    try:
        text = filepath.read_text(encoding="utf-8")
        summary = parser_cls().parse_and_save(project, text)
    except Exception as exc:  # noqa: BLE001 — 파싱 실패 광범위 캡처는 의도된 정책
        SyncLog.objects.create(
            project=project,
            file_name=filename,
            file_mtime=file_mtime,
            result=SyncLog.Result.FAILED,
            detail=f"{type(exc).__name__}: {exc}"[:500],
        )
        return SyncLog.Result.FAILED

    SyncLog.objects.create(
        project=project,
        file_name=filename,
        file_mtime=file_mtime,
        changed=True,
        result=SyncLog.Result.SUCCESS,
        detail=summary,
    )
    return SyncLog.Result.SUCCESS


def sync_project(project: Project) -> dict[str, str]:
    """프로젝트 전체 동기화 — PARSER_REGISTRY 순서대로 sync_one_file 호출.

    반환: {파일명: result} 딕셔너리.
    """
    results: dict[str, str] = {}
    for filename in PARSER_REGISTRY:
        results[filename] = sync_one_file(project, filename)

    project.last_synced_at = timezone.now()
    project.save(update_fields=["last_synced_at", "updated_at"])
    return results
