// Document checklist ticks on this device (FR6, AD-11), and what the "Open checklist"
// button under an answer opens. Pure functions that take the storage object, so
// tests/test_checklist_js.py can run them in Node with an in-memory storage. Ticks and
// "doesn't apply" choices stay in localStorage; nothing here talks to the server (NFR5).
// No Thai here (AD-6).
"use strict";

(function (root) {
  // The visit purposes, in the order the page offers them (app/ports/content.py).
  const PURPOSES = ["tourism", "family", "friends"];
  // localStorage: the ticked item ids of one checklist, as a JSON list.
  const TICK_PREFIX = "checklist:";
  // localStorage: the ids of items marked "doesn't apply to me", as a JSON list.
  const NOT_APPLICABLE_PREFIX = "checklist-na:";

  function isPurpose(value) {
    return PURPOSES.indexOf(value) >= 0;
  }

  function tickKey(purpose) {
    return TICK_PREFIX + purpose;
  }

  function notApplicableKey(purpose) {
    return NOT_APPLICABLE_PREFIX + purpose;
  }

  function isText(value) {
    return typeof value === "string" && value.trim() !== "";
  }

  // The stored ids under `key`. Unreadable, corrupt or blocked storage gives [].
  function readIds(local, key) {
    let stored;
    try {
      stored = JSON.parse(local.getItem(key) || "[]");
    } catch (error) {
      return [];
    }
    if (!Array.isArray(stored)) {
      return [];
    }
    return unique(stored.filter(isText));
  }

  function unique(ids) {
    return ids.filter(function (id, index) {
      return ids.indexOf(id) === index;
    });
  }

  // The items of a GET /api/checklists/{purpose} body that the page can show:
  // [{id, text, conditional, source}]. The source link is checked by the page
  // (https only) when it is shown. A malformed body gives [].
  function validItems(body) {
    if (!body || !Array.isArray(body.items)) {
      return [];
    }
    const seen = new Set();
    const items = [];
    for (const item of body.items) {
      if (!item || !isText(item.id) || !isText(item.text) || seen.has(item.id)) {
        continue;
      }
      seen.add(item.id);
      items.push({
        id: item.id,
        text: item.text,
        conditional: item.conditional === true,
        source: item.source || null,
      });
    }
    return items;
  }

  // The state of one checklist: {ticked: [ids], notApplicable: [ids]}. Only ids of the
  // served items are kept (removed items are ignored; new items start unticked and
  // applying); "doesn't apply" only for conditional items; an item is never both
  // (a tick wins).
  function cleanState(items, ticked, notApplicable) {
    const ids = items.map(function (item) {
      return item.id;
    });
    const conditional = items
      .filter(function (item) {
        return item.conditional;
      })
      .map(function (item) {
        return item.id;
      });
    const keptTicks = unique(ticked).filter(function (id) {
      return ids.indexOf(id) >= 0;
    });
    const keptNotApplicable = unique(notApplicable).filter(function (id) {
      return conditional.indexOf(id) >= 0 && keptTicks.indexOf(id) < 0;
    });
    return { ticked: keptTicks, notApplicable: keptNotApplicable };
  }

  // The state to show for `purpose`. `memory` ({purpose: state}) holds the state of a
  // checklist whose last save failed (storage blocked or full), so the ticks still work
  // for this visit; otherwise the stored ids are read.
  function load(local, memory, purpose, items) {
    const kept = memory[purpose];
    if (kept) {
      return cleanState(items, kept.ticked, kept.notApplicable);
    }
    return cleanState(items, readIds(local, tickKey(purpose)), readIds(local, notApplicableKey(purpose)));
  }

  // Saves `state` for `purpose` at once. Returns false when storage is blocked or full;
  // the state is then kept in `memory` for the rest of the visit.
  function save(local, memory, purpose, state) {
    try {
      local.setItem(tickKey(purpose), JSON.stringify(state.ticked));
      local.setItem(notApplicableKey(purpose), JSON.stringify(state.notApplicable));
      delete memory[purpose];
      return true;
    } catch (error) {
      memory[purpose] = { ticked: state.ticked.slice(), notApplicable: state.notApplicable.slice() };
      return false;
    }
  }

  function without(ids, id) {
    return ids.filter(function (other) {
      return other !== id;
    });
  }

  // Tick or untick `id`. Ticking clears "doesn't apply".
  function toggleTick(state, id) {
    if (state.ticked.indexOf(id) >= 0) {
      return { ticked: without(state.ticked, id), notApplicable: state.notApplicable.slice() };
    }
    return { ticked: state.ticked.concat([id]), notApplicable: without(state.notApplicable, id) };
  }

  // Mark `id` as "doesn't apply to me", or undo that. Marking clears the tick.
  function toggleNotApplicable(state, id) {
    if (state.notApplicable.indexOf(id) >= 0) {
      return { ticked: state.ticked.slice(), notApplicable: without(state.notApplicable, id) };
    }
    return { ticked: without(state.ticked, id), notApplicable: state.notApplicable.concat([id]) };
  }

  // {done, total, allDone}: only the items that apply are counted. With none applying
  // (every item marked "doesn't apply") nothing is done.
  function progress(items, state) {
    let done = 0;
    let total = 0;
    for (const item of items) {
      if (state.notApplicable.indexOf(item.id) >= 0) {
        continue;
      }
      total += 1;
      if (state.ticked.indexOf(item.id) >= 0) {
        done += 1;
      }
    }
    return { done: done, total: total, allDone: total > 0 && done === total };
  }

  // The served progress text with `{done}` and `{total}` filled in.
  function progressText(template, counts) {
    return String(template).split("{done}").join(String(counts.done)).split("{total}").join(String(counts.total));
  }

  // The known visit purposes in `value`, in PURPOSES order and each once: the
  // `checklist_purposes` of a `sources` event, or those stored with a saved exchange.
  // Anything else (unknown purposes, not a list, missing in an older saved chat) gives [].
  function validPurposes(value) {
    if (!Array.isArray(value)) {
      return [];
    }
    return PURPOSES.filter(function (purpose) {
      return value.indexOf(purpose) >= 0;
    });
  }

  // What the "Open checklist" button under an answer opens: null for no button (no
  // purposes), {purpose: "..."} for one purpose (that checklist directly), and
  // {purpose: null} for several (the purpose choice first).
  function openTarget(purposes) {
    const valid = validPurposes(purposes);
    if (!valid.length) {
      return null;
    }
    return { purpose: valid.length === 1 ? valid[0] : null };
  }

  const Checklist = {
    PURPOSES: PURPOSES,
    isPurpose: isPurpose,
    tickKey: tickKey,
    notApplicableKey: notApplicableKey,
    readIds: readIds,
    validItems: validItems,
    load: load,
    save: save,
    toggleTick: toggleTick,
    toggleNotApplicable: toggleNotApplicable,
    progress: progress,
    progressText: progressText,
    validPurposes: validPurposes,
    openTarget: openTarget,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = Checklist;
  } else {
    root.Checklist = Checklist;
  }
})(this);
