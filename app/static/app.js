// Chat page. Every visible text comes from GET /api/texts (AD-6): no Thai here.
// Answers stream from POST /api/chat as JSON Lines (AD-8); text is only appended.
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
  const messages = document.getElementById("messages");

  let texts = {};
  let answering = false;

  function render(data) {
    texts = data.texts;
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
        ask(example.text, false);
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

  function setAnswering(value) {
    answering = value;
    question.disabled = value;
    send.disabled = value;
    for (const button of exampleQuestions.querySelectorAll("button")) {
      button.disabled = value;
    }
    form.setAttribute("aria-busy", value ? "true" : "false");
    // Screen readers wait for the whole reply instead of announcing every fragment.
    messages.setAttribute("aria-busy", value ? "true" : "false");
  }

  function nearBottom() {
    const doc = document.documentElement;
    return window.innerHeight + window.scrollY >= doc.scrollHeight - 80;
  }

  function keepInView(follow) {
    if (follow) {
      window.scrollTo(0, document.documentElement.scrollHeight);
    }
  }

  // One reply: reminder (if any), streamed text, typing dots, then sources.
  function createReply() {
    const element = document.createElement("div");
    element.className = "message reply";

    const body = document.createElement("p");
    body.className = "reply-text";
    const text = document.createTextNode("");
    body.appendChild(text);

    const typing = document.createElement("span");
    typing.className = "typing";
    typing.setAttribute("aria-hidden", "true");
    for (let i = 0; i < 3; i += 1) {
      typing.appendChild(document.createElement("span"));
    }

    element.append(body, typing);
    messages.appendChild(element);

    function stopTyping() {
      typing.remove();
    }

    return {
      reminder: function () {
        const note = document.createElement("p");
        note.className = "reminder";
        note.setAttribute("role", "note");
        note.textContent = texts["personal-info-reminder"];
        element.insertBefore(note, body);
      },
      append: function (delta) {
        stopTyping();
        text.appendData(delta);
      },
      sources: function (items) {
        stopTyping();
        if (!items.length) {
          return;
        }
        const list = document.createElement("ul");
        list.className = "sources";
        for (const item of items) {
          const link = document.createElement("a");
          link.href = item.url;
          link.target = "_blank";
          link.rel = "noopener";
          link.textContent = item.title;
          const entry = document.createElement("li");
          entry.appendChild(link);
          list.appendChild(entry);
        }
        element.appendChild(list);
      },
      error: function () {
        stopTyping();
        const note = document.createElement("p");
        note.className = "error-text";
        note.setAttribute("role", "alert");
        note.textContent = texts["error"];
        element.appendChild(note);
      },
    };
  }

  // Applies one stream event. Returns true once the stream is finished.
  function handle(event, reply) {
    switch (event.type) {
      case "meta":
        if (event.personal_info_removed) {
          reply.reminder();
        }
        return false;
      case "text":
        reply.append(event.delta);
        return false;
      case "sources":
        reply.sources(event.sources);
        return false;
      case "done":
        return true;
      case "error":
        reply.error();
        return true;
      default:
        return false; // unknown events from a newer server are ignored
    }
  }

  async function stream(text, reply) {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      // Follow-up questions come in Story 1.7: no history is kept yet.
      body: JSON.stringify({ question: text, history: [] }),
    });
    if (!response.ok || !response.body) {
      throw new Error("POST /api/chat failed: " + response.status);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let streamEnded = false;
    try {
      for (;;) {
        const { value, done } = await reader.read();
        streamEnded = done;
        buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = done ? "" : lines.pop();
        for (const line of lines) {
          if (!line.trim()) {
            continue;
          }
          const event = JSON.parse(line);
          const follow = nearBottom();
          const finished = handle(event, reply);
          keepInView(follow);
          if (finished) {
            return event.type === "done";
          }
        }
        if (done) {
          throw new Error("POST /api/chat ended without done or error");
        }
      }
    } finally {
      // Also after a bad line or a throw in handle: stop the download.
      if (!streamEnded) {
        reader.cancel().catch(function () {});
      }
    }
  }

  // `fromField`: the question was typed, so the field is cleared (an example tap keeps a draft).
  async function ask(text, fromField) {
    text = text.trim();
    if (answering || !text) {
      return;
    }
    setAnswering(true);
    if (fromField) {
      question.value = "";
    }

    const bubble = document.createElement("p");
    bubble.className = "message question-bubble";
    bubble.textContent = text;
    messages.appendChild(bubble);
    const reply = createReply();
    keepInView(true);

    let answered = false;
    try {
      answered = await stream(text, reply);
    } catch (error) {
      console.error(error);
      reply.error();
    } finally {
      setAnswering(false);
    }
    // On any failure the applicant gets the question back to send again.
    if (!answered && !question.value) {
      question.value = text;
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    ask(question.value, true);
  });
  retry.addEventListener("click", load);

  load();
})();
