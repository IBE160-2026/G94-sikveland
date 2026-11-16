// Saved chats on this device (AD-3). Pure functions that take the storage objects,
// so tests/test_history_js.py can run them in Node with an in-memory storage.
// The list lives in localStorage; the id of the chat open in this tab in sessionStorage (per tab).
// Also the feedback conversation_id (AD-10), what follows a Yes/No answer (Story 2.3) and
// the "Show English" request body and response (Story 4.1).
// No Thai here (AD-6), and nothing here talks to the server.
"use strict";

(function (root) {
  // localStorage: [{id, updated, exchanges: [{question, answer, sources, reminder, checklistPurposes}]}].
  // `checklistPurposes` (Story 3.3) is missing in chats saved before it existed.
  const LIST_KEY = "conversations";
  // sessionStorage: id of the chat open in this tab, so a reload keeps it.
  const OPEN_KEY = "open-conversation";
  // sessionStorage: the single conversation stored before the saved list existed.
  const OLD_KEY = "conversation";
  // The latest chats by last activity; saving one more drops the oldest.
  const MAX_CONVERSATIONS = 20;
  // Exchanges kept per chat; older ones are dropped to keep storage small.
  const MAX_STORED = 50;
  // Must match the server's request limits (app/web/chat.py); a test checks this.
  const MAX_HISTORY = 10;
  const MAX_QUESTION_CHARS = 1000;
  const MAX_ANSWER_CHARS = 10000;
  // sessionStorage: the feedback conversation_id (UUID v4) of the chat on screen in this tab.
  // Sent only with a feedback answer; never stored in the saved chats (AD-10).
  const CONVERSATION_ID_KEY = "conversation-id";
  // A UUID v4 in lower case, as uuid4 below makes it (the server also accepts upper case).
  const UUID4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
  const FEEDBACK_ANSWERS = ["yes", "no"];

  function isText(value) {
    return typeof value === "string" && value.trim() !== "";
  }

  // Keeps only exchanges with a question and an answer; the rest (sources, reminder,
  // checklistPurposes) is kept as stored and checked when shown.
  function validExchanges(value) {
    if (!Array.isArray(value)) {
      return [];
    }
    return value.filter(function (entry) {
      return entry && isText(entry.question) && isText(entry.answer);
    });
  }

  function validConversation(value) {
    if (!value || !isText(value.id) || typeof value.updated !== "number" || !isFinite(value.updated)) {
      return null;
    }
    const exchanges = validExchanges(value.exchanges);
    if (!exchanges.length) {
      return null;
    }
    return { id: value.id, updated: value.updated, exchanges: exchanges.slice(-MAX_STORED) };
  }

  // Saved chats, newest first. Bad entries are skipped; blocked storage gives [].
  function loadList(local) {
    let stored;
    try {
      stored = JSON.parse(local.getItem(LIST_KEY) || "[]");
    } catch (error) {
      return [];
    }
    if (!Array.isArray(stored)) {
      return [];
    }
    const seen = {};
    return stored
      .map(validConversation)
      .filter(function (conversation) {
        return conversation !== null;
      })
      .sort(function (a, b) {
        return b.updated - a.updated;
      })
      .filter(function (conversation) {
        if (seen[conversation.id]) {
          return false;
        }
        seen[conversation.id] = true;
        return true;
      })
      .slice(0, MAX_CONVERSATIONS);
  }

  // Returns false when storage is blocked or full.
  function writeList(local, list) {
    try {
      if (list.length) {
        local.setItem(LIST_KEY, JSON.stringify(list));
      } else {
        local.removeItem(LIST_KEY);
      }
      return true;
    } catch (error) {
      return false;
    }
  }

  function findConversation(local, id) {
    return (
      loadList(local).find(function (conversation) {
        return conversation.id === id;
      }) || null
    );
  }

  // Stores `conversation` ({id, exchanges}) as the newest chat. The list is read again
  // first, so chats another tab saved in the meantime are kept. An empty chat is not saved.
  // Returns false when nothing was stored (storage blocked or full, or no exchanges).
  function saveConversation(local, conversation, now) {
    const exchanges = validExchanges(conversation.exchanges).slice(-MAX_STORED);
    if (!isText(conversation.id) || !exchanges.length) {
      return false;
    }
    const others = loadList(local).filter(function (saved) {
      return saved.id !== conversation.id;
    });
    const saved = { id: conversation.id, updated: now, exchanges: exchanges };
    return writeList(local, [saved].concat(others).slice(0, MAX_CONVERSATIONS));
  }

  // Adds `record` (stored only after `done`) to the open chat, saves it and marks it open
  // in this tab. Returns the updated open chat ({id, exchanges}). The chat gets its id
  // (`newId`) only once it is saved, so an id always means "was in the list". If that id
  // is no longer in the list, the chat was deleted (in another tab): it is not brought
  // back, and the new exchange starts a new chat. When storage is blocked or full the
  // exchange is kept in memory only, so follow-ups still work. A new chat started that way
  // is a new conversation for feedback: its conversation_id is dropped (with `memory`, the
  // page's in-memory copy), so the next question makes a new one (AD-10).
  function appendExchange(local, session, conversation, record, now, newId, memory) {
    let id = conversation.id;
    let exchanges = conversation.exchanges.concat([record]);
    if (id && !findConversation(local, id)) {
      id = null;
      exchanges = [record];
      dropConversationId(session, memory || { id: null });
    }
    exchanges = exchanges.slice(-MAX_STORED);
    const next = { id: id || newId, exchanges: exchanges };
    if (saveConversation(local, next, now)) {
      setOpenId(session, next.id);
      return next;
    }
    return { id: id, exchanges: exchanges };
  }

  function deleteConversation(local, id) {
    const list = loadList(local);
    const rest = list.filter(function (conversation) {
      return conversation.id !== id;
    });
    return rest.length === list.length || writeList(local, rest);
  }

  function deleteAll(local) {
    return writeList(local, []);
  }

  function setOpenId(session, id) {
    try {
      if (id) {
        session.setItem(OPEN_KEY, id);
      } else {
        session.removeItem(OPEN_KEY);
      }
    } catch (error) {
      // storage blocked: a reload then opens an empty new chat
    }
  }

  // The chat open in this tab, or null for an empty new chat (also on a fresh visit).
  function openConversation(local, session) {
    let id = null;
    try {
      id = session.getItem(OPEN_KEY);
    } catch (error) {
      return null;
    }
    if (!id) {
      return null;
    }
    const conversation = findConversation(local, id);
    if (!conversation) {
      setOpenId(session, null); // deleted in another tab, or dropped from the list
    }
    return conversation;
  }

  // Moves the conversation stored before the saved list existed into the list, once,
  // and opens it. Malformed data is dropped. Returns the new id, or null.
  function migrate(local, session, id, now) {
    let raw;
    try {
      raw = session.getItem(OLD_KEY);
    } catch (error) {
      return null;
    }
    if (raw === null) {
      return null;
    }
    let exchanges = [];
    try {
      exchanges = validExchanges(JSON.parse(raw));
    } catch (error) {
      exchanges = [];
    }
    let moved = null;
    if (exchanges.length) {
      if (!saveConversation(local, { id: id, exchanges: exchanges }, now)) {
        return null; // storage full: kept for the next load
      }
      setOpenId(session, id);
      moved = id;
    }
    try {
      session.removeItem(OLD_KEY);
    } catch (error) {
      // nothing more to do
    }
    return moved;
  }

  // At page start: move old data over first, then open this tab's chat (empty if none).
  // An empty chat (none was open, or the open one is gone: deleted in another tab or
  // dropped from the list) is a new conversation, so a leftover conversation_id is dropped.
  function startOpen(local, session, newId, now) {
    migrate(local, session, newId, now);
    const stored = openConversation(local, session);
    if (!stored) {
      dropConversationId(session, { id: null });
      return { id: null, exchanges: [] };
    }
    return { id: stored.id, exchanges: stored.exchanges };
  }

  // The request's history: the last 10 exchanges of the open chat as {question, answer}.
  // Exchanges over the server's limits are left out, so one long turn cannot block later questions.
  function historyToSend(exchanges) {
    return validExchanges(exchanges)
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

  // A local id for the saved list only; not the feedback conversation_id (AD-10).
  function createId() {
    return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
  }

  // A random UUID v4 from `cryptoObject` (the page passes the browser's crypto): randomUUID
  // where the browser has it (secure pages only), else getRandomValues, which also works
  // on plain http, e.g. a phone opening the app by the computer's address in the LAN.
  function uuid4(cryptoObject) {
    if (cryptoObject && typeof cryptoObject.randomUUID === "function") {
      try {
        const id = String(cryptoObject.randomUUID()).toLowerCase();
        if (UUID4.test(id)) {
          return id;
        }
      } catch (error) {
        // not allowed here: build one below
      }
    }
    const bytes = new Uint8Array(16);
    if (cryptoObject && typeof cryptoObject.getRandomValues === "function") {
      cryptoObject.getRandomValues(bytes);
    } else {
      for (let i = 0; i < bytes.length; i += 1) {
        bytes[i] = Math.floor(Math.random() * 256);
      }
    }
    bytes[6] = (bytes[6] & 0x0f) | 0x40; // version 4
    bytes[8] = (bytes[8] & 0x3f) | 0x80; // variant 10xx
    const hex = Array.from(bytes, function (byte) {
      return (byte + 0x100).toString(16).slice(1);
    }).join("");
    return [hex.slice(0, 8), hex.slice(8, 12), hex.slice(12, 16), hex.slice(16, 20), hex.slice(20)].join("-");
  }

  // The feedback conversation_id of the chat on screen; made with `makeId` when there is
  // none (the first question of a chat). Kept in sessionStorage, so a reload keeps it; when
  // that is blocked, in `memory` ({id}) for as long as the page is open.
  function conversationId(session, memory, makeId) {
    let stored = null;
    try {
      stored = session.getItem(CONVERSATION_ID_KEY);
    } catch (error) {
      stored = null;
    }
    let id = stored;
    if (!id || !UUID4.test(id)) {
      id = memory.id && UUID4.test(memory.id) ? memory.id : makeId();
    }
    memory.id = id;
    if (id !== stored) {
      try {
        session.setItem(CONVERSATION_ID_KEY, id);
      } catch (error) {
        // storage blocked: kept in memory only
      }
    }
    return id;
  }

  // Drops the conversation_id: new chat, reopening a saved chat, or "Yes". The next
  // question then makes a new one.
  function dropConversationId(session, memory) {
    memory.id = null;
    try {
      session.removeItem(CONVERSATION_ID_KEY);
    } catch (error) {
      // storage blocked: the memory copy is gone already
    }
  }

  // Yes/No buttons go only under a reply to category `done` that ended with `done`.
  function showsFeedback(category, answered) {
    return answered === true && category === "done";
  }

  // The body of POST /api/feedback: the conversation_id and the answer, nothing else (AD-10).
  function feedbackBody(id, answer) {
    if (!UUID4.test(String(id)) || FEEDBACK_ANSWERS.indexOf(answer) < 0) {
      throw new Error("invalid feedback answer");
    }
    return { conversation_id: id, answer: answer };
  }

  // After the server stored an answer: the text key shown under the buttons, and whether
  // the chat ends. "No": the follow-up text, and the chat goes on. "Yes": the thanks text;
  // the chat stays on screen and saved, and the next question starts a new chat.
  function afterFeedback(answer) {
    if (answer === "yes") {
      return { textKey: "feedback-thanks", ends: true };
    }
    return { textKey: "feedback-follow-up", ends: false };
  }

  // "Show English" (Story 4.1, FR7). The body of POST /api/translate: the reply text only,
  // never the reminder or the sources; null when there is no text to translate.
  function translateBody(text) {
    return isText(text) ? { text: text } : null;
  }

  // The English from a POST /api/translate response body, or null when it has none.
  function translationText(body) {
    return body && isText(body.translation) ? body.translation : null;
  }

  // At most `max` characters (whole code points), with an ellipsis when cut.
  function shorten(text, max) {
    const chars = Array.from(String(text).replace(/\s+/g, " ").trim());
    return chars.length <= max ? chars.join("") : chars.slice(0, max - 1).join("") + "\u2026";
  }

  const History = {
    LIST_KEY: LIST_KEY,
    OPEN_KEY: OPEN_KEY,
    OLD_KEY: OLD_KEY,
    MAX_CONVERSATIONS: MAX_CONVERSATIONS,
    MAX_STORED: MAX_STORED,
    MAX_HISTORY: MAX_HISTORY,
    loadList: loadList,
    findConversation: findConversation,
    saveConversation: saveConversation,
    appendExchange: appendExchange,
    startOpen: startOpen,
    deleteConversation: deleteConversation,
    deleteAll: deleteAll,
    setOpenId: setOpenId,
    openConversation: openConversation,
    migrate: migrate,
    historyToSend: historyToSend,
    createId: createId,
    shorten: shorten,
    CONVERSATION_ID_KEY: CONVERSATION_ID_KEY,
    uuid4: uuid4,
    conversationId: conversationId,
    dropConversationId: dropConversationId,
    showsFeedback: showsFeedback,
    feedbackBody: feedbackBody,
    afterFeedback: afterFeedback,
    translateBody: translateBody,
    translationText: translationText,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = History;
  } else {
    root.ChatHistory = History;
  }
})(this);
