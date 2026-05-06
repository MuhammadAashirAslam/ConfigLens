"""Parser for GitHub Actions workflow files with line-number tracking."""

from pathlib import Path
from typing import Any, Dict, Optional
from configlens.parsers.workflow_models import WorkflowFile, WorkflowJob, WorkflowStep
from configlens.parsers.yaml_loader import AnnotatedDict, AnnotatedList, load_yaml_with_line_numbers


def parse_workflow_content(content: str, path: Optional[Path] = None) -> WorkflowFile:
    """Parse GitHub Actions workflow YAML content into typed WorkflowFile with line numbers."""
    target_path = path or Path(".github/workflows/workflow.yml")
    parsed_data = load_yaml_with_line_numbers(content)

    if not isinstance(parsed_data, dict):
        return WorkflowFile(path=target_path, line_number=1, raw={})

    wf_line = getattr(parsed_data, "line_number", 1)
    name = parsed_data.get("name")
    on_trigger = parsed_data.get("on")
    permissions = parsed_data.get("permissions")

    jobs_dict: Dict[str, WorkflowJob] = {}
    raw_jobs = parsed_data.get("jobs")

    if isinstance(raw_jobs, dict):
        for job_id, job_data in raw_jobs.items():
            if not isinstance(job_data, dict):
                continue

            # Determine job line number
            if isinstance(raw_jobs, AnnotatedDict):
                job_line = raw_jobs.get_line(str(job_id), getattr(job_data, "line_number", wf_line))
            else:
                job_line = getattr(job_data, "line_number", wf_line)

            steps_list: list[WorkflowStep] = []
            raw_steps = job_data.get("steps")

            if isinstance(raw_steps, list):
                for step_data in raw_steps:
                    if not isinstance(step_data, dict):
                        continue

                    step_line = getattr(step_data, "line_number", job_line)
                    step = WorkflowStep(
                        line_number=step_line,
                        name=step_data.get("name"),
                        step_id=step_data.get("id"),
                        uses=step_data.get("uses"),
                        run=step_data.get("run"),
                        with_args=dict(step_data.get("with", {})) if isinstance(step_data.get("with"), dict) else {},
                        env=dict(step_data.get("env", {})) if isinstance(step_data.get("env"), dict) else {},
                        raw=dict(step_data),
                    )
                    steps_list.append(step)

            job = WorkflowJob(
                job_id=str(job_id),
                line_number=job_line,
                name=job_data.get("name"),
                runs_on=job_data.get("runs-on"),
                timeout_minutes=job_data.get("timeout-minutes"),
                permissions=job_data.get("permissions"),
                steps=steps_list,
                raw=dict(job_data),
            )
            jobs_dict[str(job_id)] = job

    return WorkflowFile(
        path=target_path,
        line_number=wf_line,
        name=str(name) if name is not None else None,
        on=on_trigger,
        permissions=permissions,
        jobs=jobs_dict,
        raw=dict(parsed_data),
    )


def parse_workflow_file(path: Path) -> WorkflowFile:
    """Read and parse a GitHub Actions workflow file from disk."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return WorkflowFile(path=path, line_number=1, raw={})
    return parse_workflow_content(content, path=path)
