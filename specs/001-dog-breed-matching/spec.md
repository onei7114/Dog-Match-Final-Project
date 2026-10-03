# Feature Specification: Dog Breed Matching

**Feature Branch**: `001-dog-breed-matching`

**Created**: 2026-10-03

**Status**: Draft

**Input**: User description: Dog owners and dog fans upload a dog photo and receive the breed the dog most closely resembles, including a reference photo and breed name, a 1-100% similarity score, and a welcoming, responsive experience. Use the project's `Dog-Breeds-Dataset`; support modern Chrome, Firefox, and Edge. Social features and dog adoption are out of scope.

## Clarifications

### Session 2026-10-03

- Q: Should a match score be allowed to display 0%, or must the scale start at 1%? → A: Match scores use a 1-100% scale; 0% is not displayed.
- Q: Is the current release target of at least 80% correct top-match breed labels across 100 held-out dog photos acceptable? → A: Keep the 80% target across 100 held-out photos as the initial release threshold.
- Q: How quickly should the page be ready to accept a photo after a user opens it on a typical broadband connection? → A: The page should be ready within five seconds.

## Target users
- Dog owners who don’t know their dogs breed
- Dog fans who want to know what dog breed they have a picture of

## Problem
People may see or own a dog and they will not know what breed it is. Users want a way to identify the breed from a picture.

## User Scenarios & Testing

### User Story 1 - Get a Breed Match (Priority: P1)

A dog owner or dog fan opens the standalone page, uploads a JPG photo of a dog, and receives the closest visual match from the project reference collection. The result shows the matched reference image, the breed name taken from its containing folder, and a similarity percentage.

**Why this priority**: This is the core user need and the central value of the application.

**Independent Test**: Upload a valid JPG with a known dog image and verify that a result is displayed with a reference image, its folder title, and a 1-100% similarity score.

**Acceptance Scenarios**:

1. **Given** the page is ready and the user has a valid JPG dog photo, **When** the user submits it, **Then** the page displays the closest matching dataset JPG, the title of its containing breed folder, and a similarity score from 1% to 100%.
2. **Given** a match is displayed, **When** the user reviews the result, **Then** the score is identified as visual similarity to the reference image and not as the probability that the breed identification is correct.

---

### User Story 2 - Understand and Recover from an Upload Problem (Priority: P2)

A user receives clear feedback when the selected image cannot be used or matching cannot be completed, and can choose another photo without mistaking an error for a successful result.

**Why this priority**: Honest, recoverable errors keep users oriented and protect them from misleading breed claims.

**Independent Test**: Submit unsupported and unreadable files, and simulate an unavailable or empty reference collection; verify clear feedback and no fabricated match.

**Acceptance Scenarios**:

1. **Given** the user selects a non-JPG or unreadable file, **When** they submit it, **Then** the page explains the problem and allows them to choose another image.
2. **Given** the reference collection cannot be used or no valid candidate can be found, **When** matching is attempted, **Then** the page reports that no result is available and does not show a false match or score.

---

### Edge Cases

- The selected image has an unsupported format, is corrupt, or cannot be read.
- The image contains no dog, multiple dogs, or a dog too small or obscured for a useful comparison.
- The reference collection is missing, empty, or contains no readable JPG images.
- Multiple reference images appear equally close, or the closest result is still a weak visual match.
- Matching cannot be completed; an error must not be presented as a successful result.
- The page is viewed on a narrow mobile screen
## Requirements

### Functional Requirements

- **FR-001**: The application MUST provide a standalone page through which a user can submit a dog photo and view a match without creating an account.
- **FR-002**: The application MUST accept JPG photos and provide a clear, actionable message for unsupported, corrupt, or unreadable files.
- **FR-003**: The application MUST compare a submitted photo with the JPG reference images in `Dog-Breeds-Dataset` and select the closest available image.
- **FR-004**: A successful result MUST display the selected reference JPG and the title of the folder containing that image as the breed name.
- **FR-005**: A successful result MUST show an integer similarity score from 1% through 100%; it MUST NOT display 0%. The score MUST be described as visual image similarity, not as breed-identification probability or certainty.
- **FR-006**: The method used to calculate or convert the similarity score MUST be documented, and result messaging MUST communicate that the displayed match is the closest dataset match rather than a guaranteed breed identification.
- **FR-007**: The application MUST provide clear failure states when the user image cannot be matched or the reference collection is unavailable; it MUST NOT fabricate a breed, reference image, or score.
- **FR-008**: The page MUST present a happy, welcoming visual tone and keep upload, progress, result, and error information easy to scan.
- **FR-009**: The page MUST work in the latest stable releases of Chrome, Firefox, and Edge at the time of testing on desktop and mobile screen sizes, and MUST keep text and controls readable without incoherent overlap.
- **FR-010**: Social networking and dog adoption functionality MUST NOT be included in this feature.

### Acceptance Criteria

| Requirement | Acceptance criteria |
|-------------|---------------------|
| FR-001 | A first-time visitor can upload a photo and view a match without creating or signing into an account. |
| FR-002 | An unsupported or unreadable upload produces an actionable error and no match result. |
| FR-003 | For a valid upload, the selected image has the highest similarity score among readable dataset JPGs under the documented scoring method. |
| FR-004 | The result image is present in the dataset, and its displayed breed name matches its containing folder title. |
| FR-005 | A successful result displays an integer from 1% through 100%, labeled as image similarity rather than breed probability. |
| FR-006 | Project documentation explains the similarity scoring and percentage conversion, and result messaging states that the match is not guaranteed breed identification. |
| FR-007 | If no candidate can be evaluated or the reference collection is unavailable, the page shows a clear failure state without fabricating a match or score. |
| FR-008 | A review of upload, progress, result, and error states confirms approachable language, consistent cheerful styling, and scannable primary information. |
| FR-009 | The primary flow works in the latest stable releases of Chrome, Firefox, and Edge at the time of testing on desktop and mobile viewports without blocking overlap or horizontal scrolling. |
| FR-010 | A scope review confirms the feature contains no social networking or dog adoption workflows. |

### Key Entities

- **Uploaded Dog Photo**: A user-selected JPG image submitted for comparison; assumed to be used only to produce the current result and not retained afterward.
- **Breed Reference Image**: A JPG in the project dataset, associated with the title of its containing breed folder.
- **Breed Match Result**: The selected reference image, its folder title, and the visual similarity percentage shown to the user.

## Success Criteria
### Measurable Outcomes

- **SC-001**: In a usability test, at least 9 out of 10 first-time participants can submit a valid JPG and identify the displayed breed-folder title and similarity score without assistance within two minutes.
- **SC-002**: Every successful result in the acceptance test set contains all three required values: a dataset reference image, its containing folder title, and a 1-100% similarity score.
- **SC-003**: On a separate test set of at least 100 dog photos with known breed labels, none of which are included in the reference collection, at least 80% of displayed breed names match the known labels. This is the confirmed initial release threshold. The test set and scoring method are documented.
- **SC-004**: At least 95% of valid JPG submissions in the acceptance test set produce either a complete match result or a clear actionable failure message; no submission appears to succeed with missing or fabricated result data.
- **SC-005**: Users can complete the primary flow in the latest stable releases of Chrome, Firefox, and Edge at the time of testing at desktop and mobile viewport sizes, with no blocking overlap or horizontal scrolling in the tested flow.
- **SC-006**: On a connection with at least 25 Mbps download and 5 Mbps upload speed, the page is ready to accept a photo within five seconds of opening.

## Assumptions

- The existing `Dog-Breeds-Dataset` remains available to the application, and each image's parent folder title is the user-facing breed label.
- The typical submission contains one clearly visible dog. Images with no discernible dog or several equally prominent dogs may receive a clear no-result or limitation message.
- Uploaded photos are processed for the requested match and are not retained after the result is produced.
- The 80% held-out breed-label agreement target is an initial product acceptance target, not a guarantee for every photo or breed.
- The broadband test condition for SC-007 is at least 25 Mbps download and 5 Mbps upload speed.
- Similarity percentage represents image similarity only; it is not a calibrated probability of breed identity.
