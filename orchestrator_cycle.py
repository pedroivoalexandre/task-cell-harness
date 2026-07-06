from pathlib import Path

from task_cell import TaskCell


IMPLEMENTER_TEMPLATE = Path("templates/gemini_implementer_prompt.md")
REVIEWER_TEMPLATE = Path("templates/codex_reviewer_prompt.md")
REPORT_TEMPLATE = Path("templates/task_cell_report.md")


def _render_template(template_path, values):
    text = Path(template_path).read_text(encoding="utf-8")
    for key, value in values.items():
        if isinstance(value, list):
            rendered = "\n".join(f"- {item}" for item in value) if value else "- none"
        else:
            rendered = "" if value is None else str(value)
        text = text.replace(f"{{{{{key}}}}}", rendered)
    return text


def generate_implementation_prompt(cell):
    return _render_template(
        IMPLEMENTER_TEMPLATE,
        {
            "task_id": cell.task_id,
            "title": cell.title,
            "objective": cell.objective,
            "context": cell.context,
            "inputs": cell.inputs,
            "constraints": cell.constraints,
            "allowed_actions": cell.allowed_actions,
            "acceptance_criteria": cell.acceptance_criteria,
        },
    )


def generate_reviewer_prompt(cell, implementation_summary):
    return _render_template(
        REVIEWER_TEMPLATE,
        {
            "task_id": cell.task_id,
            "title": cell.title,
            "implementation_summary": implementation_summary,
            "acceptance_criteria": cell.acceptance_criteria,
        },
    )


def generate_report(cell, implementation_summary, review_summary, files_changed, tests_executed, risks, pending_items, final_status, recommendation):
    return _render_template(
        REPORT_TEMPLATE,
        {
            "task_id": cell.task_id,
            "objective": cell.objective,
            "implementation_summary": implementation_summary,
            "review_summary": review_summary,
            "files_changed": files_changed,
            "tests_executed": tests_executed,
            "acceptance_criteria": cell.acceptance_criteria,
            "risks": risks,
            "pending_items": pending_items,
            "final_status": final_status,
            "recommendation": recommendation,
        },
    )


def run_simulated_cycle(cell_data, workspace):
    workspace = Path(workspace)
    cell = TaskCell.from_dict(cell_data)
    cell.status = "implementing"
    implementation_prompt = generate_implementation_prompt(cell)
    implementation_summary = "Implementation completed in simulated dry-run mode."
    implementation_path = workspace / f"{cell.task_id}.implementation.md"
    implementation_path.write_text(implementation_summary + "\n", encoding="utf-8")

    cell.status = "reviewing"
    reviewer_prompt = generate_reviewer_prompt(cell, implementation_summary)
    review_summary = "Review approved in simulated dry-run mode."
    review_decision = "approved"
    review_path = workspace / f"{cell.task_id}.review.md"
    review_path.write_text(review_summary + "\n", encoding="utf-8")

    cell.status = review_decision
    report_text = generate_report(
        cell,
        implementation_summary=implementation_summary,
        review_summary=review_summary,
        files_changed=[str(implementation_path), str(review_path)],
        tests_executed=["simulated"],
        risks=["No real agents were executed."],
        pending_items=[],
        final_status=cell.status,
        recommendation="Proceed with the next phase after approval.",
    )
    report_path = workspace / f"{cell.task_id}.report.md"
    report_path.write_text(report_text, encoding="utf-8")

    result = {
        "cell": cell.to_dict(),
        "implementation_prompt": implementation_prompt,
        "reviewer_prompt": reviewer_prompt,
        "implementation_summary": implementation_summary,
        "review_summary": review_summary,
        "review_decision": review_decision,
        "implementation_path": str(implementation_path),
        "review_path": str(review_path),
        "report_path": str(report_path),
    }
    cell.report = str(report_path)
    cell.dump(workspace / f"{cell.task_id}.json")
    return result
