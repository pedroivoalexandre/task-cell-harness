import json
from pathlib import Path

from execution_context import utc_now


class ReportBuilder:
    def build_payload(
        self,
        task_id,
        title,
        status,
        review_result=None,
        execution_context=None,
        artifacts=None,
        logs=None,
    ):
        return {
            "task_id": task_id,
            "title": title or "",
            "status": status,
            "generated_at": utc_now(),
            "execution_context": execution_context.to_dict() if execution_context else None,
            "artifacts": artifacts or [],
            "logs": logs or [],
            "review": review_result or {},
        }

    def build_markdown(self, payload):
        review = payload.get("review") or {}
        errors = review.get("errors") or []
        error_section = ""
        if errors:
            error_section = "- Errors:\n" + "".join(f"  - {error}\n" for error in errors)

        execution = payload.get("execution_context") or {}
        execution_section = ""
        if execution:
            execution_section = (
                "\n## Execution Context\n"
                f"- Execution ID: {execution.get('execution_id')}\n"
                f"- Executor: {execution.get('executor_name')}\n"
                f"- Role: {execution.get('executor_role')}\n"
            )

        artifact_section = ""
        artifacts = payload.get("artifacts") or []
        if artifacts:
            artifact_section = "\n## Artifacts\n" + "".join(
                f"- {artifact.get('name')} ({artifact.get('kind')}): {artifact.get('path')}\n"
                for artifact in artifacts
            )

        return (
            f"# Task Report: {payload['task_id']}\n\n"
            f"## Title\n{payload.get('title') or ''}\n\n"
            f"## Status\n{payload.get('status')}\n\n"
            f"## Notes\nFake task executed without calling external agents.\n\n"
            f"## Review\n"
            f"- Decision: {review.get('decision')}\n"
            f"- Summary: {review.get('summary')}\n"
            + error_section
            + execution_section
            + artifact_section
            + f"\n## Finished at\n{payload.get('generated_at')}\n"
        )

    def write_report(
        self,
        markdown_path,
        task_id,
        title,
        status,
        review_result=None,
        execution_context=None,
        artifacts=None,
        logs=None,
    ):
        markdown_path = Path(markdown_path)
        payload = self.build_payload(
            task_id,
            title,
            status,
            review_result=review_result,
            execution_context=execution_context,
            artifacts=artifacts,
            logs=logs,
        )
        markdown_path.write_text(self.build_markdown(payload), encoding="utf-8")
        json_path = markdown_path.with_suffix(".json")
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return {"markdown": markdown_path, "json": json_path, "payload": payload}
