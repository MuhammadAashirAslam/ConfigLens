"""Rule detecting broad or unconstrained port exposure in Docker Compose services."""

import re
from pathlib import Path
from typing import List
from configlens.models import Category, Finding, Severity
from configlens.parsers.compose_models import ComposeFile
from configlens.rules.base import Rule, parse_inline_suppressions

# Sensitive internal service / database ports that should not be exposed to 0.0.0.0
SENSITIVE_PORTS = {"5432", "3306", "6379", "27017", "9200", "9300", "11211", "2181", "9092"}


class ComposeBroadPortsRule(Rule):
    """Flags services exposing sensitive internal or database ports broadly to 0.0.0.0."""

    id = "compose-broad-ports"
    title = "Broad port exposure for internal services"
    description = "Database and internal datastore ports should not be bound broadly to 0.0.0.0 without localhost restriction."
    severity = Severity.HIGH
    category = Category.DOCKER_COMPOSE

    def check(self, file_path: Path, parsed: ComposeFile) -> List[Finding]:
        """Check all service port mappings for broad sensitive port exposure."""
        findings: List[Finding] = []
        suppressions = parse_inline_suppressions(file_path)

        for svc in parsed.services.values():
            for port in svc.ports:
                port_str = str(port).strip()

                # Detect bare port like "5432:5432" or "0.0.0.0:5432:5432"
                host_port = ""
                container_port = ""

                parts = port_str.split(":")
                if len(parts) == 2:
                    # "host:container"
                    host_port, container_port = parts[0], parts[1]
                elif len(parts) == 3:
                    # "ip:host:container"
                    ip, host_port, container_port = parts[0], parts[1], parts[2]
                    if ip not in {"0.0.0.0", ""}:
                        continue  # explicitly bound to non-zero IP (e.g. 127.0.0.1)

                if container_port in SENSITIVE_PORTS or host_port in SENSITIVE_PORTS:
                    if not self.is_line_suppressed(suppressions, svc.line_number):
                        findings.append(
                            self.create_finding(
                                file_path=file_path,
                                line_number=svc.line_number,
                                message=f"Service '{svc.name}' exposes internal port '{port_str}' broadly to all host network interfaces.",
                                suggested_fix=f"Bind port to localhost ('127.0.0.1:{host_port}:{container_port}') or use internal Docker network without port publication.",
                            )
                        )

        return findings
