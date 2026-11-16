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

  const checklistButton = document.getElementById("checklist-button");
  const checklistPanel = document.getElementById("checklist-panel");
  const checklistTitle = document.getElementById("checklist-title");
  const checklistClose = document.getElementById("checklist-close");
  const checklistChoice = document.getElementById("checklist-choice");
  const checklistChoosePurpose = document.getElementById("checklist-choose-purpose");
  const checklistPurposes = document.getElementById("checklist-purposes");
  const checklistView = document.getElementById("checklist-view");
  const checklistPurposeName = document.getElementById("checklist-purpose-name");
  const checklistChangePurpose = document.getElementById("checklist-change-purpose");
  const checklistStatus = document.getElementById("checklist-status");
  const checklistLoading = document.getElementById("checklist-loading");
  const checklistProgress = document.getElementById("checklist-progress");
  const checklistAllDone = document.getElementById("checklist-all-done");
  const checklistList = document.getElementById("checklist-items");
  const checklistFailed = document.getElementById("checklist-failed");
  const checklistError = document.getElementById("checklist-error");
  const checklistRetry = document.getElementById("checklist-retry");
  const checklistTranslate = document.getElementById("checklist-translate");
  // Behind the full-screen panel: made inert while it is open, so focus cannot reach them.
  const behindPanel = [document.querySelector("header.top"), document.querySelector("main"), form];

  // Storage logic lives in history.js (loaded first): saved chats in localStorage on
  // this device, the open chat's id in this tab's sessionStorage (AD-3).
  const Chats = window.ChatHistory;
  const local = storage("localStorage");
  const session = storage("sessionStorage");
  // Length of a saved chat's first question in the list.
  const TITLE_CHARS = 80;
  // Checklist ticks live in checklist.js (loaded first): localStorage on this device only.
  const Lists = window.Checklist;
  // Checklists whose last save failed (storage blocked or full): ticked for this visit only.
  const checklistMemory = {};
  // The checklist on screen: its purpose, served items, state and DOM rows by item id.
  let checklistPurpose = null;
  let checklistItems = [];
  let checklistState = { ticked: [], notApplicable: [] };
  let checklistRows = {};
  // Counts checklist loads; a response for an older one (purpose changed, view closed) is ignored.
  let checklistRequest = 0;
  // The button that opened the checklist (top bar or under an answer); focus goes back to it.
  let checklistOpener = null;
  // True once "Show English" was tapped in the checklist view; reset when the view closes
  // or the purpose changes.
  let checklistEnglish = false;

  let texts = {};
  let answering = false;
  // True while POST /api/feedback is in flight (see setSendingFeedback).
  let sendingFeedback = false;
  // The chat on screen. `id` is null until its first exchange is stored, so an empty
  // new chat never becomes a list item. Each exchange: {question, answer, sources, reminder,
  // checklistPurposes}; only {question, answer} of the last 10 is sent.
  let current = emptyChat();
  // The feedback id of this chat when sessionStorage is blocked (kept by history.js).
  const feedbackMemory = { id: null };
  // True after "Yes": the chat stays on screen, and the next question starts a new chat.
  let chatEnded = false;

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
    checklistButton.textContent = data.texts["checklist-button"];
    checklistTitle.textContent = data.texts["checklist-title"];
    checklistClose.textContent = data.texts["checklist-back"];
    checklistChoosePurpose.textContent = data.texts["checklist-choose-purpose"];
    checklistChangePurpose.textContent = data.texts["checklist-change-purpose"];
    checklistLoading.textContent = data.texts["checklist-loading"];
    checklistRetry.setAttribute("aria-label", data.texts["checklist-retry"]);
    checklistTranslate.textContent = data.texts["translate-button"];

    checklistPurposes.replaceChildren();
    for (const purpose of Lists.PURPOSES) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "checklist-purpose";
      button.dataset.purpose = purpose;
      button.textContent = data.texts["checklist-purpose-" + purpose];
      button.addEventListener("click", function () {
        choosePurpose(purpose);
      });
      checklistPurposes.appendChild(button);
    }

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
      // The "Open checklist" button comes back too; an older exchange without purposes,
      // or with unknown ones only, gets none.
      reply.checklistOpen(Lists.validPurposes(entry.checklistPurposes));
      // Every saved reply ended with `done`; its English is never stored, so the button
      // comes back instead.
      reply.translate(entry.answer);
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
    // Screen readers wait for the whole reply instead of announcing every fragment.
    messages.setAttribute("aria-busy", value ? "true" : "false");
    setControlsDisabled(busy());
  }

  // While a feedback answer is being sent, nothing else can start either: a late "Yes"
  // must end the chat it belongs to, not one opened or asked in the meantime.
  function setSendingFeedback(value) {
    sendingFeedback = value;
    setControlsDisabled(busy());
  }

  function busy() {
    return answering || sendingFeedback;
  }

  function setControlsDisabled(value) {
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
    // Only buttons not yet answered; an answered or closed question stays disabled.
    for (const button of messages.querySelectorAll('.feedback[data-state="open"] button')) {
      button.disabled = value;
    }
    form.setAttribute("aria-busy", value ? "true" : "false");
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
      // "Open checklist" under an answer that cites a checklist-linked source (AD-11):
      // one purpose opens that checklist, several open the purpose choice.
      checklistOpen: function (purposes) {
        const target = Lists.openTarget(purposes);
        if (!target) {
          return;
        }
        stopTyping();
        const button = document.createElement("button");
        button.type = "button";
        button.className = "checklist-open";
        button.setAttribute("aria-controls", "checklist-panel");
        // With one purpose the button names it, since it opens that checklist directly.
        button.textContent = target.purpose
          ? texts["checklist-open"] + ": " + texts["checklist-purpose-" + target.purpose]
          : texts["checklist-open"];
        button.addEventListener("click", function () {
          openChecklist(button, target.purpose);
        });
        element.appendChild(button);
      },
      // "Show English" under a finished reply (Story 4.1, FR7): after the sources and the
      // checklist button, before the feedback buttons. Only the reply text is sent.
      translate: function (answer) {
        const body = Chats.translateBody(answer);
        if (!body) {
          return;
        }
        const button = document.createElement("button");
        button.type = "button";
        button.className = "translate-button";
        button.textContent = texts["translate-button"];
        button.addEventListener("click", function () {
          translateReply(element, button, body);
        });
        element.appendChild(button);
      },
      error: function () {
        stopTyping();
        // A failed reply is never saved, so it keeps no "Open checklist" button either.
        const open = element.querySelector(".checklist-open");
        if (open) {
          open.remove();
        }
        const note = document.createElement("p");
        note.className = "error-text";
        note.setAttribute("role", "alert");
        note.textContent = texts["error"];
        element.appendChild(note);
      },
      // Yes/No buttons under a live feedback question (never on a replayed chat).
      feedback: function () {
        addFeedbackButtons(element);
      },
    };
  }

  // The Yes and No buttons, and below them the text that follows an answer. Only the
  // latest feedback question can be answered: earlier unanswered buttons close.
  function addFeedbackButtons(element) {
    closeFeedbackGroups();
    const group = document.createElement("div");
    group.className = "feedback";
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", texts["feedback-question"]);
    group.dataset.state = "open";
    const buttons = [];
    for (const answer of ["yes", "no"]) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "feedback-button";
      button.dataset.answer = answer;
      button.textContent = texts["feedback-" + answer];
      button.addEventListener("click", function () {
        sendFeedback(group, buttons, answer);
      });
      buttons.push(button);
      group.appendChild(button);
    }
    // Announced when it appears (role status), like the rest of the conversation.
    const note = document.createElement("p");
    note.className = "feedback-note";
    note.setAttribute("role", "status");
    note.hidden = true;
    element.append(group, note);
  }

  // Every feedback group not closed yet (open or sending) closes for good; a request
  // still in flight for one of them is then ignored when it ends.
  function closeFeedbackGroups() {
    for (const group of messages.querySelectorAll('.feedback:not([data-state="closed"])')) {
      group.dataset.state = "closed";
      for (const button of group.querySelectorAll("button")) {
        button.disabled = true;
      }
    }
  }

  // POST /api/feedback. The buttons are disabled from the first tap, so one tap is one row,
  // and nothing else can start until the request ends. On failure the buttons come back
  // with the fixed error text, so the applicant can tap again.
  async function sendFeedback(group, buttons, answer) {
    if (group.dataset.state !== "open" || busy()) {
      return;
    }
    group.dataset.state = "sending";
    for (const button of buttons) {
      button.disabled = true;
    }
    const reply = group.parentElement;
    const failed = reply.querySelector(".feedback-error");
    if (failed) {
      failed.remove();
    }
    setSendingFeedback(true);
    let stored = false;
    try {
      const id = Chats.conversationId(session, feedbackMemory, newConversationId);
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify(Chats.feedbackBody(id, answer)),
      });
      if (response.status !== 204) {
        throw new Error("POST /api/feedback failed: " + response.status);
      }
      stored = true;
    } catch (error) {
      console.error(error);
    }
    setSendingFeedback(false);
    if (group.dataset.state !== "sending") {
      return; // closed meanwhile: a late result changes nothing
    }
    if (!stored) {
      group.dataset.state = "open";
      for (const button of buttons) {
        button.disabled = busy();
      }
      const note = document.createElement("p");
      note.className = "error-text feedback-error";
      note.setAttribute("role", "alert");
      note.textContent = texts["error"];
      reply.appendChild(note);
      return;
    }
    group.dataset.state = "closed";
    for (const button of buttons) {
      if (button.dataset.answer === answer) {
        // The chosen answer stays marked (one-shot actions, not toggle buttons).
        button.classList.add("feedback-chosen");
        button.setAttribute("aria-current", "true");
      }
    }
    const result = Chats.afterFeedback(answer);
    const note = group.nextElementSibling;
    const follow = nearBottom();
    note.textContent = texts[result.textKey];
    note.hidden = false;
    if (result.ends) {
      endChat();
    }
    keepInView(follow);
  }

  // POST /api/translate for one reply. The button is disabled while the request is in
  // flight. On success it is replaced by the English (lang="en") and the Thai, sources and
  // other buttons stay; on failure the fixed error text is shown and the button comes back.
  // A result for a reply that left the screen (new chat, another chat opened) is ignored.
  // The English is kept on the page only, never stored with the chat.
  async function translateReply(reply, button, body) {
    if (button.disabled) {
      return;
    }
    button.disabled = true;
    const failed = reply.querySelector(".translate-error");
    if (failed) {
      failed.remove();
    }
    let english = null;
    try {
      const response = await fetch("/api/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        throw new Error("POST /api/translate failed: " + response.status);
      }
      english = Chats.translationText(await response.json());
      if (english === null) {
        throw new Error("POST /api/translate gave no translation");
      }
    } catch (error) {
      console.error(error);
    }
    if (!reply.isConnected || !button.isConnected) {
      return; // the reply left the screen meanwhile
    }
    const follow = nearBottom();
    if (english === null) {
      button.disabled = false;
      const note = document.createElement("p");
      note.className = "error-text translate-error";
      note.setAttribute("role", "alert");
      note.textContent = texts["error"];
      button.after(note);
    } else {
      const hadFocus = document.activeElement === button;
      const paragraph = document.createElement("p");
      paragraph.className = "translation";
      paragraph.lang = "en";
      paragraph.textContent = english;
      button.replaceWith(paragraph);
      if (hadFocus) {
        // The button is gone: focus stays at the same place in the reply.
        paragraph.tabIndex = -1;
        paragraph.focus();
      }
    }
    keepInView(follow);
  }

  function newConversationId() {
    return Chats.uuid4(window.crypto);
  }

  // After "Yes": the chat stays on screen and in the saved chats, its conversation_id is
  // dropped, and every other feedback group in it closes. The next question starts a new
  // chat; a reload opens an empty new chat too.
  function endChat() {
    chatEnded = true;
    Chats.dropConversationId(session, feedbackMemory);
    Chats.setOpenId(session, null);
    closeFeedbackGroups();
  }

  // Applies one stream event. Returns true once the stream is finished.
  // `record` collects the exchange as shown, to store it after `done`.
  // `info.category` is the reply's category; it is never stored with the exchange.
  function handle(event, reply, record, info) {
    switch (event.type) {
      case "meta":
        info.category = typeof event.category === "string" ? event.category : null;
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
        // Set by the server from the fixed checklists; kept with the exchange so the
        // button comes back when the chat is shown again.
        record.checklistPurposes = event.checklist === true ? Lists.validPurposes(event.checklist_purposes) : [];
        reply.checklistOpen(record.checklistPurposes);
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

  async function stream(text, reply, record, info) {
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
          const finished = handle(event, reply, record, info);
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
    if (busy() || !text) {
      return;
    }
    if (chatEnded) {
      // After "Yes": this question opens an empty new chat and is asked there.
      showChat(emptyChat());
    }
    // The feedback id (AD-10): made at the first question of a chat, kept for the next ones.
    Chats.conversationId(session, feedbackMemory, newConversationId);
    setAnswering(true);
    if (fromField) {
      question.value = "";
    }

    addQuestionBubble(text);
    const reply = createReply();
    keepInView(true);

    const record = { question: "", answer: "", sources: [], reminder: false, checklistPurposes: [] };
    const info = { category: null };
    let answered = false;
    try {
      answered = await stream(text, reply, record, info);
      // Stored only after `done`, never after `error` (AD-3).
      if (answered && record.question.trim() && record.answer.trim()) {
        storeExchange(record);
      }
      // Every reply that ended with `done` gets "Show English", before any feedback buttons.
      if (answered) {
        reply.translate(record.answer);
      }
      // The feedback question gets Yes/No buttons; a replayed one never does (FR5).
      if (Chats.showsFeedback(info.category, answered)) {
        reply.feedback();
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
    current = Chats.appendExchange(local, session, current, record, Date.now(), Chats.createId(), feedbackMemory);
  }

  // New chat, a reopened chat, or the open one deleted: a new conversation for feedback,
  // so the next question makes a new conversation_id (AD-10).
  function showChat(conversation) {
    current = conversation;
    chatEnded = false;
    Chats.setOpenId(session, current.id);
    Chats.dropConversationId(session, feedbackMemory);
    showConversation();
  }

  function startNewChat() {
    if (busy()) {
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
    if (busy()) {
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
    if (busy()) {
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
    if (busy() || !window.confirm(texts["confirm-delete-chat"])) {
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
    if (busy() || !window.confirm(texts["confirm-delete-all-chats"])) {
      return;
    }
    Chats.deleteAll(local);
    showChat(emptyChat());
    renderHistoryList();
    historyClose.focus();
  }

  // --- Document checklist (Story 3.2, FR6) ----------------------------------------------
  // Opening, ticking and closing never touch the chat, its saved chats or an answer that is
  // still arriving, so the Checklist button works while busy. Ticks and "doesn't apply"
  // choices are saved on this device only (checklist.js); the only request is the
  // checklist itself, GET /api/checklists/{purpose} (NFR5).

  // `opener` gets focus back on close. Without `purpose` (the top-bar button, or an answer
  // linked to several purposes) the view starts with the purpose choice; with one, that
  // checklist opens directly, as if it had been chosen.
  function openChecklist(opener, purpose) {
    checklistOpener = opener;
    showPurposeChoice();
    setBehindPanelInert(true);
    checklistPanel.hidden = false;
    document.body.classList.add("panel-open");
    // With a purpose, choosePurpose moves focus to the checklist heading (focus moves once).
    if (purpose) {
      choosePurpose(purpose);
    } else {
      checklistClose.focus();
    }
  }

  function closeChecklist() {
    checklistRequest += 1; // a load still in flight changes nothing
    checklistPanel.hidden = true;
    document.body.classList.remove("panel-open");
    setBehindPanelInert(false);
    const opener = checklistOpener && checklistOpener.isConnected ? checklistOpener : checklistButton;
    checklistOpener = null;
    opener.focus();
  }

  function showPurposeChoice() {
    checklistRequest += 1;
    checklistPurpose = null;
    checklistItems = [];
    checklistRows = {};
    checklistEnglish = false;
    checklistTranslate.hidden = true;
    checklistList.replaceChildren();
    checklistFailed.hidden = true;
    checklistView.hidden = true;
    checklistChoice.hidden = false;
  }

  // "Change purpose": back to the choice, with focus on the purpose that was open.
  function changePurpose() {
    const previous = checklistPurpose;
    showPurposeChoice();
    const button = checklistPurposes.querySelector('[data-purpose="' + previous + '"]');
    (button || checklistClose).focus();
  }

  function choosePurpose(purpose) {
    if (!Lists.isPurpose(purpose)) {
      return;
    }
    checklistPurpose = purpose;
    checklistPurposeName.textContent = texts["checklist-purpose-" + purpose];
    checklistStatus.hidden = true;
    checklistChoice.hidden = true;
    checklistView.hidden = false;
    checklistPurposeName.focus();
    loadChecklist();
  }

  // Loads the open purpose's checklist; on failure the fixed error text with a retry.
  async function loadChecklist() {
    const purpose = checklistPurpose;
    if (!Lists.isPurpose(purpose)) {
      return;
    }
    checklistRequest += 1;
    const request = checklistRequest;
    checklistRetry.disabled = true;
    // The loading text stays until the items or the error appear.
    checklistTranslate.hidden = true;
    checklistProgress.hidden = true;
    checklistAllDone.hidden = true;
    checklistLoading.hidden = false;
    checklistStatus.hidden = false;
    let items = [];
    let failed = null;
    try {
      const response = await fetch("/api/checklists/" + purpose, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("GET /api/checklists failed: " + response.status);
      }
      items = Lists.validItems(await response.json());
      if (!items.length) {
        throw new Error("GET /api/checklists gave no items");
      }
    } catch (error) {
      failed = error;
    }
    if (request !== checklistRequest) {
      return; // purpose changed or view closed meanwhile
    }
    checklistRetry.disabled = false;
    checklistLoading.hidden = true;
    if (failed) {
      console.error(failed);
      checklistError.textContent = texts["error"];
      checklistFailed.hidden = false;
      return;
    }
    checklistItems = items;
    checklistState = Lists.load(local, checklistMemory, purpose, items);
    renderChecklist();
  }

  // One row per item: a large tick box with the text, "doesn't apply to me" for a
  // conditional item, and the source link (https only, new tab).
  function renderChecklist() {
    const rows = {};
    const list = [];
    checklistItems.forEach(function (item, index) {
      const row = document.createElement("li");
      row.className = "checklist-item";

      const tickLabel = document.createElement("label");
      tickLabel.className = "checklist-tick";
      const tick = document.createElement("input");
      tick.type = "checkbox";
      tick.className = "checklist-box";
      const text = document.createElement("span");
      text.className = "checklist-text";
      text.id = "checklist-item-" + index;
      text.textContent = item.text;
      tickLabel.append(tick, text);
      tick.addEventListener("change", function () {
        changeChecklist(Lists.toggleTick(checklistState, item.id));
      });
      row.appendChild(tickLabel);
      if (checklistEnglish) {
        addChecklistEnglish(row, item);
      }

      let notApplicable = null;
      if (item.conditional) {
        const label = document.createElement("label");
        label.className = "checklist-na";
        notApplicable = document.createElement("input");
        notApplicable.type = "checkbox";
        notApplicable.className = "checklist-na-box";
        // Read out with the item it belongs to.
        notApplicable.setAttribute("aria-describedby", text.id);
        const naText = document.createElement("span");
        naText.textContent = texts["checklist-not-applicable"];
        label.append(notApplicable, naText);
        notApplicable.addEventListener("change", function () {
          changeChecklist(Lists.toggleNotApplicable(checklistState, item.id));
        });
        row.appendChild(label);
      }

      const source = safeSources([item.source])[0];
      if (source) {
        const link = document.createElement("a");
        link.className = "checklist-source";
        link.href = source.url;
        link.target = "_blank";
        link.rel = "noopener";
        link.textContent = source.title;
        row.appendChild(link);
      }

      rows[item.id] = { row: row, tick: tick, notApplicable: notApplicable };
      list.push(row);
    });
    checklistRows = rows;
    checklistList.replaceChildren.apply(checklistList, list);
    checklistTranslate.hidden = checklistEnglish;
    // After a retry the focused retry button is hidden: focus goes to the heading.
    const retryHadFocus = checklistFailed.contains(document.activeElement);
    checklistFailed.hidden = true;
    refreshChecklist();
    checklistProgress.hidden = false;
    checklistStatus.hidden = false;
    if (retryHadFocus) {
      checklistPurposeName.focus();
    }
  }

  // "Show English" in the checklist view (Story 4.1): the stored English under every item,
  // served with the checklist, so no request and no model call. It stays until the view
  // closes or the purpose changes.
  function showChecklistEnglish() {
    if (checklistEnglish || !checklistItems.length) {
      return;
    }
    checklistEnglish = true;
    for (const item of checklistItems) {
      addChecklistEnglish(checklistRows[item.id].row, item);
    }
    checklistTranslate.hidden = true;
    // The button is gone: focus goes to the heading of the checklist.
    checklistPurposeName.focus();
  }

  // The English of one item, right under its tick box and text (not inside the label, so
  // tapping it ticks nothing).
  function addChecklistEnglish(row, item) {
    if (!item.en) {
      return;
    }
    const english = document.createElement("p");
    english.className = "checklist-en";
    english.lang = "en";
    english.textContent = item.en;
    row.firstElementChild.after(english);
  }

  // A tick or "doesn't apply" change: saved at once on this device, never sent anywhere.
  function changeChecklist(state) {
    checklistState = state;
    Lists.save(local, checklistMemory, checklistPurpose, state);
    refreshChecklist();
  }

  // Shows the state: ticks, "doesn't apply" (its item dimmed; ticking it clears that
  // choice), progress, all done.
  function refreshChecklist() {
    for (const item of checklistItems) {
      const row = checklistRows[item.id];
      const ticked = checklistState.ticked.indexOf(item.id) >= 0;
      const notApplicable = checklistState.notApplicable.indexOf(item.id) >= 0;
      row.tick.checked = ticked;
      if (row.notApplicable) {
        row.notApplicable.checked = notApplicable;
      }
      row.row.dataset.state = notApplicable ? "not-applicable" : ticked ? "ticked" : "open";
    }
    const counts = Lists.progress(checklistItems, checklistState);
    checklistProgress.textContent = Lists.progressText(texts["checklist-progress"], counts);
    checklistAllDone.textContent = texts["checklist-all-done"];
    checklistAllDone.hidden = !counts.allDone;
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
  checklistButton.addEventListener("click", function () {
    openChecklist(checklistButton, null);
  });
  checklistClose.addEventListener("click", closeChecklist);
  checklistChangePurpose.addEventListener("click", changePurpose);
  checklistRetry.addEventListener("click", loadChecklist);
  checklistTranslate.addEventListener("click", showChecklistEnglish);
  // On the document, so Escape also works when focus is on the page body (e.g. after a
  // click on panel text).
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !checklistPanel.hidden) {
      closeChecklist();
    }
  });

  current = Chats.startOpen(local, session, Chats.createId(), Date.now());
  load();
})();
