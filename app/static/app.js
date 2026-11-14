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
  const demoLabel = document.getElementById("demo-label");

  let texts = {};
  let answering = false;

  // The conversation lives in this tab only (AD-3): reload keeps it, closing the tab drops it.
  // Each entry: {question, answer, sources, reminder}; only {question, answer} is sent.
  const STORAGE_KEY = "conversation";
  // Must match the server's request limits (app/web/chat.py); a test checks this.
  const MAX_HISTORY = 10;
  const MAX_QUESTION_CHARS = 1000;
  const MAX_ANSWER_CHARS = 10000;
  // Shown again after a reload; older exchanges are dropped to keep storage small.
  const MAX_STORED = 50;

  function loadConversation() {
    try {
      const stored = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "[]");
      if (!Array.isArray(stored)) {
        return [];
      }
      return stored.filter(function (entry) {
        return (
          entry &&
          typeof entry.question === "string" &&
          entry.question.trim() &&
          typeof entry.answer === "string" &&
          entry.answer.trim()
        );
      });
    } catch (error) {
      return []; // storage blocked or unreadable: start a new conversation
    }
  }

  function saveConversation(conversation) {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(conversation));
    } catch (error) {
      console.error(error); // storage blocked or full: the answer is still shown
    }
  }

  function historyToSend() {
    return loadConversation()
      .filter(function (entry) {
        return (
          entry.question.trim().length <= MAX_QUESTION_CHARS &&
          entry.answer.trim().length <= MAX_ANSWER_CHARS
        );
      })
      .slice(-MAX_HISTORY)
      .map(function (entry) {
        return { question: entry.question, answer: entry.answer };
      });
  }

  // One check for live and replayed source links.
  function safeSources(items) {
    if (!Array.isArray(items)) {
      return [];
    }
    return items
      .filter(function (item) {
        return item && typeof item.title === "string" && /^https:\/\//.test(item.url);
      })
      .map(function (item) {
        return { title: item.title, url: item.url };
      });
  }

  function render(data) {
    texts = data.texts;
    // In demo mode (MOCK_LLM=true) the "demo-label" text stays visible at the top.
    demoLabel.textContent = data.texts["demo-label"];
    demoLabel.hidden = data.demo_mode !== true;
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

    showConversation();

    loadFailed.hidden = true;
    chat.hidden = false;
    form.hidden = false;
  }

  function addQuestionBubble(text) {
    const bubble = document.createElement("p");
    bubble.className = "message question-bubble";
    bubble.textContent = text;
    messages.appendChild(bubble);
  }

  function showConversation() {
    messages.replaceChildren();
    for (const entry of loadConversation()) {
      addQuestionBubble(entry.question);
      const reply = createReply();
      if (entry.reminder) {
        reply.reminder();
      }
      reply.append(entry.answer);
      reply.sources(safeSources(entry.sources));
    }
    keepInView(true);
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
  // `record` collects the exchange as shown, to store it after `done`.
  function handle(event, reply, record) {
    switch (event.type) {
      case "meta":
        // Only the cleaned question is ever stored (AD-3, AD-4).
        record.question = typeof event.clean_question === "string" ? event.clean_question : "";
        record.reminder = Boolean(event.personal_info_removed);
        if (event.personal_info_removed) {
          reply.reminder();
        }
        return false;
      case "text":
        record.answer += event.delta;
        reply.append(event.delta);
        return false;
      case "sources":
        record.sources = safeSources(event.sources);
        reply.sources(record.sources);
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

  async function stream(text, reply, record) {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify({ question: text, history: historyToSend() }),
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
          const finished = handle(event, reply, record);
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

    addQuestionBubble(text);
    const reply = createReply();
    keepInView(true);

    const record = { question: "", answer: "", sources: [], reminder: false };
    let answered = false;
    try {
      answered = await stream(text, reply, record);
      // Stored only after `done`, never after `error` (AD-3).
      if (answered && record.question.trim() && record.answer.trim()) {
        const conversation = loadConversation();
        conversation.push(record);
        saveConversation(conversation.slice(-MAX_STORED));
      }
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
