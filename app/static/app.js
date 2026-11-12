// Chat page. Every visible text comes from GET /api/texts (AD-6): no Thai here.
// Sending a question is wired in Story 1.6.
"use strict";

(function () {
  const chat = document.getElementById("chat");
  const form = document.getElementById("question-form");
  const loadFailed = document.getElementById("load-failed");
  const retry = document.getElementById("retry");
  const question = document.getElementById("question");
  const send = document.getElementById("send");
  const privacyNotice = document.getElementById("privacy-notice");
  const exampleQuestions = document.getElementById("example-questions");

  function render(data) {
    privacyNotice.textContent = data.texts["privacy-notice"];
    question.placeholder = data.texts["question-placeholder"];
    question.setAttribute("aria-label", data.texts["question-placeholder"]);
    send.textContent = data.texts["send-button"];

    exampleQuestions.replaceChildren();
    for (const example of data.example_questions) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "example-question";
      button.dataset.id = example.id;
      button.textContent = example.text;
      button.addEventListener("click", function () {
        question.value = example.text;
        question.focus();
      });
      exampleQuestions.appendChild(button);
    }

    loadFailed.hidden = true;
    chat.hidden = false;
    form.hidden = false;
  }

  async function load() {
    retry.disabled = true;
    try {
      const response = await fetch("/api/texts", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("GET /api/texts failed: " + response.status);
      }
      render(await response.json());
    } catch (error) {
      console.error(error);
      chat.hidden = true;
      form.hidden = true;
      loadFailed.hidden = false;
    } finally {
      retry.disabled = false;
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
  });
  retry.addEventListener("click", load);

  load();
})();
