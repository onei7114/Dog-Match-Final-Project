<!--
Sync Impact Report
Version change: 1.1.0 -> 1.2.0
Modified principles: II. Faithful, Traceable Breed Matching (expanded to require a similarity percentage).
Added principles: none.
Added sections: none.
Removed sections: none; all existing principles and sections are retained.
Follow-up TODO: Confirm the original ratification date.
-->
# Dog Match Constitution

## Core Principles

### I. Python Web Application with CLI Operations
The product MUST remain a Python application with a browser-based user experience and a
CLI entry point for running or operating the application. The web interface MUST let a user
submit a dog photograph and receive a breed-match result. Operational commands and user-facing
workflows MUST have clear, documented responsibilities.

### II. Faithful, Traceable Breed Matching
The application MUST accept JPG dog photographs, compare them against JPG images in
`Dog-Breeds-Dataset`, and return the closest matching dataset image together with the title of
the folder containing that image. The match MUST retain this image-and-folder provenance; the
application MUST NOT present an unsupported breed certainty when it only computes image
similarity. The result MUST include a similarity percentage from 0% through 100% that compares
the uploaded image with the selected closest dataset image. The result MUST identify this value
as an image-similarity score, not as the probability that the dog's breed matches. The scoring
method and any conversion to a percentage MUST be documented.

### III. Tested and Typed Python
All production Python code MUST have type hints. All application code MUST have relevant unit
tests, and the project MUST maintain strictly greater than 80% automated test coverage, measured
and reported by the project's coverage tooling. Changes MUST include tests for their behavior and
failure cases; coverage MUST be checked before merge.

### IV. Resilient Interaction
Every API call and every browser local-storage operation MUST handle failure explicitly, preserve a usable state where possible, and provide a clear user-facing error when recovery requires user action. Failures MUST NOT be reported as successful matches or saves.

### V. Simplicity and Explicit Behavior
The implementation MUST prefer the simplest design that meets the requirements and MUST avoid
unneeded abstractions. Input validation, image matching behavior, and user-visible error states
MUST be explicit and testable. New dependencies or complexity MUST be justified by a concrete
requirement.

### VI. Happy, Welcoming User Experience
The user interface MUST feel happy, friendly, and welcoming through approachable language and
cheerful visual styling. This tone MUST remain consistent across the upload, matching, result,
and error states, and MUST NOT compromise readability.

## Application and Data Constraints

The local `Dog-Breeds-Dataset` is the reference collection for image matching. The returned
match MUST use an image from that collection and identify its source folder by its title. The
application MUST validate uploaded files as supported JPG images before processing them and
handle invalid, unreadable, or unmatched input without exposing internal errors to the user.
The matching method and its limitations MUST be documented so results are not represented as
veterinary advice or guaranteed breed identification.

## Development Workflow and Quality Gates

Changes MUST be reviewed for constitution compliance. Before merge, the automated test suite
MUST pass, measured coverage MUST be greater than 80%, and production Python type hints MUST be
present. Tests MUST cover the changed behavior, including relevant invalid input, API failure,
and local-storage failure paths.

## Governance

This constitution governs project design and delivery. Amendments MUST update this document,
explain their rationale, and increment the version according to semantic versioning: MAJOR for
incompatible governance changes, MINOR for new or materially expanded requirements, and PATCH
for clarifications that do not change requirements. Reviewers MUST verify compliance with the
principles and quality gates for each change. When another project document conflicts with this
constitution, the conflict MUST be resolved or explicitly amended before the affected work is
accepted.

**Version**: 1.2.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-10-03
