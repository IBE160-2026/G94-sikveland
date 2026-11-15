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
  const topBar = document.getElementById("top-bar");

  const historyButton = document.getElementById("history-button");
  const newChatButton = document.getElementById("new-chat-button");
  const historyPanel = document.getElementById("history-panel");
  const historyTitle = document.getElementById("history-title");
  const historyClose = document.getElementById("history-close");
  const historyList = document.getElementById("history-list");
  const historyEmpty = document.getElementById("history-empty");
  const deleteAllButton = document.getElementById("delete-all-chats");
  // Behind the full-screen panel: made inert while it is open, so focus cannot reach them.
  const behindPanel = [document.querySelector("header.top"), document.querySelector("main"), form];

  // Storage logic lives in history.js (loaded first): saved chats in localStorage on
  // this device, the open chat's id in this tab's sessionStorage (AD-3).
  const Chats = window.ChatHistory;
  const local = storage("localStorage");
  const session = storage("sessionStorage");
  // Length of a saved chat's first question in the list.
  const TITLE_CHARS = 80;

  let texts = {};
  let answering = false;
  // The chat on screen. `id` is null until its first exchange is stored, so an empty
  // new chat never becomes a list item. Each exchange: {question, answer, sources, reminder};
  // only {question, answer} of the last 10 is sent.
  let current = emptyChat();

  // Some browsers throw on merely reading `window.localStorage` when storage is blocked.
  function storage(name) {
    try {
      return window[name];
    } catch (error) {
      return null;
    }
  }

  function emptyChat() {
    return { id: null, exchanges: [] };
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
    historyButton.textContent = data.texts["history-button"];
    newChatButton.textContent = data.texts["new-chat-button"];
    historyTitle.textContent = data.texts["history-title"];
    historyClose.textContent = data.texts["history-close"];
    historyEmpty.textContent = data.texts["history-empty"];
    deleteAllButton.textContent = data.texts["delete-all-chats"];

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
    topBar.hidden = false;
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
    for (const entry of current.exchanges) {
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
      topBar.hidden = true;
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
    newChatButton.disabled = value;
    historyButton.disabled = value;
    for (const button of exampleQuestions.querySelectorAll("button")) {
      button.disabled = value;
    }
    for (const button of historyPanel.querySelectorAll("button")) {
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
      body: JSON.stringify({ question: text, history: Chats.historyToSend(current.exchanges) }),
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
        storeExchange(record);
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

  // The open chat keeps its exchanges in memory too, so follow-ups work even when
  // storage is blocked or full; then the answer is shown but not saved.
  function storeExchange(record) {
    current = Chats.appendExchange(local, session, current, record, Date.now(), Chats.createId());
  }

  function showChat(conversation) {
    current = conversation;
    Chats.setOpenId(session, current.id);
    showConversation();
  }

  function startNewChat() {
    if (answering) {
      return;
    }
    showChat(emptyChat());
    window.scrollTo(0, 0);
  }

  function formatDate(time) {
    try {
      return new Date(time).toLocaleDateString(document.documentElement.lang || undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch (error) {
      return "";
    }
  }

  // Saved chats, newest first: the first question shortened, the date, a delete button.
  function renderHistoryList() {
    const list = Chats.loadList(local);
    historyList.replaceChildren();
    for (const conversation of list) {
      const title = Chats.shorten(conversation.exchanges[0].question, TITLE_CHARS);

      const reopen = document.createElement("button");
      reopen.type = "button";
      reopen.className = "history-open";
      const titleText = document.createElement("span");
      titleText.className = "history-question";
      titleText.textContent = title;
      const date = document.createElement("span");
      date.className = "history-date";
      date.textContent = formatDate(conversation.updated);
      reopen.append(titleText, date);
      reopen.addEventListener("click", function () {
        reopenChat(conversation.id);
      });

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "history-delete";
      remove.textContent = texts["delete-chat"];
      remove.setAttribute("aria-label", texts["delete-chat"] + ": " + title);
      remove.addEventListener("click", function () {
        deleteChat(conversation.id);
      });

      const item = document.createElement("li");
      item.className = "history-item";
      item.append(reopen, remove);
      historyList.appendChild(item);
    }
    historyEmpty.hidden = list.length > 0;
    deleteAllButton.hidden = list.length === 0;
  }

  function openHistory() {
    if (answering) {
      return;
    }
    renderHistoryList();
    setBehindPanelInert(true);
    historyPanel.hidden = false;
    document.body.classList.add("panel-open");
    historyClose.focus();
  }

  function closeHistory() {
    historyPanel.hidden = true;
    document.body.classList.remove("panel-open");
    setBehindPanelInert(false);
    historyButton.focus();
  }

  function setBehindPanelInert(value) {
    for (const element of behindPanel) {
      element.toggleAttribute("inert", value);
    }
  }

  function reopenChat(id) {
    if (answering) {
      return;
    }
    // Read again: another tab may have deleted it. Then the panel stays open with the new list.
    const stored = Chats.findConversation(local, id);
    if (!stored) {
      renderHistoryList();
      historyClose.focus();
      return;
    }
    closeHistory();
    showChat({ id: stored.id, exchanges: stored.exchanges });
  }

  function deleteChat(id) {
    if (answering || !window.confirm(texts["confirm-delete-chat"])) {
      return;
    }
    Chats.deleteConversation(local, id);
    if (id === current.id) {
      showChat(emptyChat());
    }
    renderHistoryList();
    historyClose.focus();
  }

  function deleteAllChats() {
    if (answering || !window.confirm(texts["confirm-delete-all-chats"])) {
      return;
    }
    Chats.deleteAll(local);
    showChat(emptyChat());
    renderHistoryList();
    historyClose.focus();
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    ask(question.value, true);
  });
  retry.addEventListener("click", load);
  newChatButton.addEventListener("click", startNewChat);
  historyButton.addEventListener("click", openHistory);
  historyClose.addEventListener("click", closeHistory);
  deleteAllButton.addEventListener("click", deleteAllChats);
  historyPanel.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeHistory();
    }
  });

  current = Chats.startOpen(local, session, Chats.createId(), Date.now());
  load();
})();
