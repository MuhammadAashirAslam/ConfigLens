"""Unit tests for Dockerfile configuration debt rules with good and bad fixtures."""

from pathlib import Path
from configlens.parsers.dockerfile_parser import parse_dockerfile_file
from configlens.rules.dockerfile import (
    DockerfileBakedSecretsRule,
    DockerfileLatestTagRule,
    DockerfileRunningAsRootRule,
    MissingDockerignoreRule,
    MissingHealthcheckRule,
    MultipleRunLayersRule,
    UncachedPkgManagerRule,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "dockerfile"
GOOD_DF = FIXTURES_DIR / "good_dockerfile" / "Dockerfile"
BAD_DF = FIXTURES_DIR / "bad_dockerfile" / "Dockerfile"


def test_latest_tag_rule():
    """Verify latest tag rule triggers on python:latest and passes on pinned."""
    rule = DockerfileLatestTagRule()

    good_parsed = parse_dockerfile_file(GOOD_DF)
    assert len(rule.check(GOOD_DF, good_parsed)) == 0

    bad_parsed = parse_dockerfile_file(BAD_DF)
    findings = rule.check(BAD_DF, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "dockerfile-latest-tag"
    assert "python:latest" in findings[0].message


def test_running_as_root_rule():
    """Verify running as root rule triggers when USER instruction is absent."""
    rule = DockerfileRunningAsRootRule()

    good_parsed = parse_dockerfile_file(GOOD_DF)
    assert len(rule.check(GOOD_DF, good_parsed)) == 0

    bad_parsed = parse_dockerfile_file(BAD_DF)
    findings = rule.check(BAD_DF, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "dockerfile-running-as-root"


def test_multiple_run_layers_rule():
    """Verify multiple run layers rule triggers on consecutive RUN instructions."""
    rule = MultipleRunLayersRule()

    good_parsed = parse_dockerfile_file(GOOD_DF)
    assert len(rule.check(GOOD_DF, good_parsed)) == 0

    bad_parsed = parse_dockerfile_file(BAD_DF)
    findings = rule.check(BAD_DF, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "dockerfile-multiple-run-layers"


def test_multiple_run_layers_multi_stage_builder_caching():
    """Verify consecutive RUN instructions in intermediate builder stage are permitted for caching."""
    from configlens.parsers.dockerfile_parser import parse_dockerfile_content

    multi_stage = """FROM golang:1.22 AS builder
WORKDIR /src
RUN go mod download
RUN go build -o /bin/app .

FROM alpine:3.19
USER appuser
COPY --from=builder /bin/app /bin/app
CMD ["/bin/app"]
"""
    parsed = parse_dockerfile_content(multi_stage)
    rule = MultipleRunLayersRule()
    findings = rule.check(Path("Dockerfile"), parsed)
    assert len(findings) == 0


def test_missing_healthcheck_rule():
    """Verify missing healthcheck rule triggers when CMD exists without HEALTHCHECK."""
    rule = MissingHealthcheckRule()

    good_parsed = parse_dockerfile_file(GOOD_DF)
    assert len(rule.check(GOOD_DF, good_parsed)) == 0

    bad_parsed = parse_dockerfile_file(BAD_DF)
    findings = rule.check(BAD_DF, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "dockerfile-missing-healthcheck"


def test_baked_secrets_rule():
    """Verify baked-in secrets rule triggers on sensitive ENV declaration."""
    rule = DockerfileBakedSecretsRule()

    good_parsed = parse_dockerfile_file(GOOD_DF)
    assert len(rule.check(GOOD_DF, good_parsed)) == 0

    bad_parsed = parse_dockerfile_file(BAD_DF)
    findings = rule.check(BAD_DF, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "dockerfile-baked-secrets"
    assert "DB_PASSWORD" in findings[0].message


def test_uncached_pkg_manager_rule():
    """Verify uncached package manager rule triggers on uncleaned apt-get."""
    rule = UncachedPkgManagerRule()

    good_parsed = parse_dockerfile_file(GOOD_DF)
    assert len(rule.check(GOOD_DF, good_parsed)) == 0

    bad_parsed = parse_dockerfile_file(BAD_DF)
    findings = rule.check(BAD_DF, bad_parsed)
    assert len(findings) >= 1
    assert any(f.rule_id == "dockerfile-uncached-pkg-manager" for f in findings)


def test_missing_dockerignore_rule():
    """Verify missing dockerignore rule triggers on broad COPY without .dockerignore."""
    rule = MissingDockerignoreRule()

    good_parsed = parse_dockerfile_file(GOOD_DF)
    assert len(rule.check(GOOD_DF, good_parsed)) == 0

    bad_parsed = parse_dockerfile_file(BAD_DF)
    findings = rule.check(BAD_DF, bad_parsed)
    assert len(findings) == 1
    assert findings[0].rule_id == "dockerfile-missing-dockerignore"
