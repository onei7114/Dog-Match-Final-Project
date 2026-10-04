"use strict";

const form = document.querySelector("#upload-form");
const fileInput = document.querySelector("#dog-photo");
const submitButton = document.querySelector("#submit-button");
const loadingMessage = document.querySelector("#loading-message");
const errorMessage = document.querySelector("#error-message");
const resultPanel = document.querySelector("#result-panel");
const breedName = document.querySelector("#breed-name");
const similarityScore = document.querySelector("#similarity-score");
const resultDisclaimer = document.querySelector("#result-disclaimer");
const referenceImage = document.querySelector("#reference-image");

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
  resultPanel.hidden = true;
}

function clearResult() {
  resultPanel.hidden = true;
  referenceImage.removeAttribute("src");
  breedName.textContent = "";
  similarityScore.textContent = "";
  resultDisclaimer.textContent = "";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorMessage.hidden = true;
  clearResult();

  const file = fileInput.files && fileInput.files[0];
  if (!file) {
    showError("Choose a JPG or JPEG photo before continuing.");
    fileInput.focus();
    return;
  }
  if (!/^image\/jpeg$/i.test(file.type) && !/\.jpe?g$/i.test(file.name)) {
    showError("Choose a JPG or JPEG photo and try again.");
    fileInput.focus();
    return;
  }

  submitButton.disabled = true;
  loadingMessage.hidden = false;
  try {
    const formData = new FormData();
    formData.append("file", file, file.name);
    const response = await fetch("/api/v1/matches", {
      method: "POST",
      body: formData,
      headers: { Accept: "application/json" },
    });
    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new Error("The matching service returned an unreadable response. Please try again.");
    }
    if (!response.ok) {
      throw new Error(payload?.error?.message || "The photo could not be matched. Please try again.");
    }
    if (
      typeof payload.breed_name !== "string" ||
      !Number.isInteger(payload.similarity_percent) ||
      payload.similarity_percent < 1 ||
      payload.similarity_percent > 100 ||
      typeof payload.reference_image_url !== "string" ||
      typeof payload.disclaimer !== "string"
    ) {
      throw new Error("The matching service returned an incomplete result. Please try again.");
    }
    const imageUrl = new URL(payload.reference_image_url, window.location.origin);
    if (imageUrl.origin !== window.location.origin) {
      throw new Error("The matching service returned an invalid reference photo.");
    }

    breedName.textContent = payload.breed_name;
    similarityScore.textContent = `${payload.similarity_percent}%`;
    resultDisclaimer.textContent = payload.disclaimer;
    referenceImage.src = imageUrl.href;
    referenceImage.onerror = () => {
      clearResult();
      showError("The matching photo could not be loaded. Please submit your photo again.");
    };
    resultPanel.hidden = false;
  } catch (error) {
    const message = error instanceof Error
      ? error.message
      : "The photo could not be matched. Please try again.";
    showError(message);
  } finally {
    loadingMessage.hidden = true;
    submitButton.disabled = false;
  }
});
