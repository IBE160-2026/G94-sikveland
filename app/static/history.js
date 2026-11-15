// Saved chats on this device (AD-3). Pure functions that take the storage objects,
// so tests/test_history_js.py can run them in Node with an in-memory storage.
// The list lives in localStorage; the id of the chat open in this tab in sessionStorage (per tab).
// No Thai here (AD-6), and nothing here talks to the server.
"use strict";

(function (root) {
  // localStorage: [{id, updated, exchanges: [{question, answer, sources, reminder}]}].
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

  function isText(value) {
    return typeof value === "string" && value.trim() !== "";
  }

  // Keeps only exchanges with a question and an answer; the rest is checked when shown.
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
  // exchange is kept in memory only, so follow-ups still work.
  function appendExchange(local, session, conversation, record, now, newId) {
    let id = conversation.id;
    let exchanges = conversation.exchanges.concat([record]);
    if (id && !findConversation(local, id)) {
      id = null;
      exchanges = [record];
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
  function startOpen(local, session, newId, now) {
    migrate(local, session, newId, now);
    const stored = openConversation(local, session);
    return stored ? { id: stored.id, exchanges: stored.exchanges } : { id: null, exchanges: [] };
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
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = History;
  } else {
    root.ChatHistory = History;
  }
})(this);
