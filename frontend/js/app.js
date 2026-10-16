const AUTH_KEY = "clarity_access_token";
const EMAIL_KEY = "clarity_email";
const authView = document.querySelector("#auth-view");
const workspaceView = document.querySelector("#workspace-view");
const authForm = document.querySelector("#auth-form");
const authError = document.querySelector("#auth-error");
const authSwitch = document.querySelector("#auth-switch");
const authSwitchLabel = document.querySelector("#auth-switch-label");
const authSubmit = document.querySelector("#auth-submit");
const chatForm = document.querySelector("#chat-form");
const chatQuestion = document.querySelector("#chat-question");
const chatMessages = document.querySelector("#chat-messages");
const chatEmpty = document.querySelector("#chat-empty");
const chatError = document.querySelector("#chat-error");
const chatSubmit = document.querySelector("#chat-submit");
const conversationList = document.querySelector("#conversation-list");
const documentList = document.querySelector("#document-list");
const documentFile = document.querySelector("#document-file");
const accountEmail = document.querySelector("#account-email");
const signOutButton = document.querySelector("#sign-out");
const workspaceNotice = document.querySelector("#workspace-notice");
const toast = document.querySelector("#toast");

let isRegistering = false;
let activeConversationId = null;
let toastTimeout;

function token() {
  return localStorage.getItem(AUTH_KEY);
}

function showError(element, message) {
  element.textContent = message;
  element.hidden = false;
}

function clearError(element) {
  element.textContent = "";
  element.hidden = true;
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const accessToken = token();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  if (options.body instanceof URLSearchParams) {
    headers.set("Content-Type", "application/x-www-form-urlencoded");
  } else if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  let response;
  try {
    response = await fetch(path, { ...options, headers });
  } catch {
    throw new Error("Could not reach the API. Check that the app server is running.");
  }
  if (response.status === 204) {
    return null;
  }
  let body;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (!response.ok) {
    if (response.status === 401 && accessToken) {
      signOut();
    }
    const detail = typeof body?.detail === "string"
      ? body.detail
      : Array.isArray(body?.detail)
        ? body.detail.map((item) => item.msg).filter(Boolean).join(" ")
        : "The request could not be completed.";
    throw new Error(detail);
  }
  return body;
}

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  window.clearTimeout(toastTimeout);
  toastTimeout = window.setTimeout(() => {
    toast.hidden = true;
  }, 4500);
}

function showSignedOut() {
  localStorage.removeItem(AUTH_KEY);
  localStorage.removeItem(EMAIL_KEY);
  activeConversationId = null;
  isRegistering = false;
  authForm.reset();
  authSubmit.textContent = "Sign in";
  authSwitchLabel.textContent = "New here?";
  authSwitch.textContent = "Create an account";
  document.querySelector("#auth-password").autocomplete = "current-password";
  authView.hidden = false;
  workspaceView.hidden = true;
  accountEmail.hidden = true;
  signOutButton.hidden = true;
  conversationList.replaceChildren();
  documentList.replaceChildren();
  clearError(authError);
  clearError(chatError);
}

function showSignedIn() {
  authView.hidden = true;
  workspaceView.hidden = false;
  accountEmail.textContent = localStorage.getItem(EMAIL_KEY) || "";
  accountEmail.hidden = false;
  signOutButton.hidden = false;
  chatQuestion.focus();
}

function signOut() {
  showSignedOut();
}

function renderConversations(conversations) {
  conversationList.replaceChildren();
  if (conversations.length === 0) {
    const empty = document.createElement("li");
    empty.className = "list-empty";
    empty.textContent = "Your saved conversations will appear here.";
    conversationList.append(empty);
    return;
  }
  for (const conversation of conversations) {
    const item = document.createElement("li");
    item.className = "sidebar-list-item";
    const open = document.createElement("button");
    open.type = "button";
    open.className = "sidebar-list-label";
    open.textContent = conversation.title;
    open.title = conversation.title;
    open.addEventListener("click", () => openConversation(conversation.id));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "list-remove";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `Delete conversation ${conversation.title}`);
    remove.addEventListener("click", () => removeConversation(conversation.id));
    item.append(open, remove);
    conversationList.append(item);
  }
}

function renderDocuments(documents) {
  documentList.replaceChildren();
  if (documents.length === 0) {
    const empty = document.createElement("li");
    empty.className = "list-empty";
    empty.textContent = "Upload PDFs to ask questions about them.";
    documentList.append(empty);
    return;
  }
  for (const document of documents) {
    const item = document.createElement("li");
    item.className = "document-list-item";
    const name = document.createElement("span");
    name.className = "document-name";
    name.textContent = document.filename;
    name.title = document.filename;
    const status = document.createElement("span");
    status.className = `document-status status-${document.index_status}`;
    status.textContent = document.index_status;
    status.title = document.index_error || document.index_status;
    item.append(name, status);
    if (document.index_status !== "indexed") {
      const retry = document.createElement("button");
      retry.type = "button";
      retry.className = "document-action";
      retry.textContent = "Retry";
      retry.addEventListener("click", () => reindexDocument(document.id));
      item.append(retry);
    }
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "list-remove";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `Delete document ${document.filename}`);
    remove.addEventListener("click", () => removeDocument(document.id));
    item.append(remove);
    documentList.append(item);
  }
}

async function refreshConversations() {
  renderConversations(await api("/api/conversations/"));
}

async function refreshDocuments() {
  const documents = await api("/api/documents/");
  renderDocuments(documents);
  const indexedCount = documents.filter((document) => document.index_status === "indexed").length;
  workspaceNotice.textContent = indexedCount
    ? `${indexedCount} document${indexedCount === 1 ? "" : "s"} ready to search. Ask a question below.`
    : "Upload a text-based PDF to get started. Add your AI provider settings in .env to enable indexing and answers.";
}

function clearChat() {
  for (const child of [...chatMessages.children]) {
    if (child !== chatEmpty) {
      child.remove();
    }
  }
  chatEmpty.hidden = false;
  chatQuestion.value = "";
  clearError(chatError);
}

function renderMessage(message) {
  chatEmpty.hidden = true;
  const article = document.createElement("article");
  article.className = `message message-${message.role}`;
  const author = document.createElement("strong");
  author.className = "message-author";
  author.textContent = message.role === "assistant" ? "Clarity" : "You";
  const content = document.createElement("p");
  content.className = "message-content";
  content.textContent = message.content;
  article.append(author, content);
  if (message.role === "assistant" && message.sources?.length) {
    const sources = document.createElement("div");
    sources.className = "answer-sources";
    const heading = document.createElement("h3");
    heading.textContent = "Sources";
    sources.append(heading);
    for (const source of message.sources) {
      const card = document.createElement("section");
      card.className = "answer-source";
      const title = document.createElement("strong");
      title.textContent = `[${source.citation}] ${source.filename}`;
      const excerpt = document.createElement("p");
      excerpt.textContent = source.excerpt;
      card.append(title, excerpt);
      sources.append(card);
    }
    article.append(sources);
  }
  chatMessages.append(article);
  article.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function openConversation(id) {
  try {
    const messages = await api(`/api/conversations/${id}/messages`);
    activeConversationId = id;
    clearChat();
    for (const message of messages) {
      renderMessage(message);
    }
  } catch (error) {
    showError(chatError, error.message);
  }
}

async function removeConversation(id) {
  try {
    await api(`/api/conversations/${id}`, { method: "DELETE" });
    if (activeConversationId === id) {
      activeConversationId = null;
      clearChat();
    }
    await refreshConversations();
  } catch (error) {
    showError(chatError, error.message);
  }
}

async function removeDocument(id) {
  try {
    await api(`/api/documents/${id}`, { method: "DELETE" });
    await refreshDocuments();
    showToast("Document deleted.");
  } catch (error) {
    showToast(error.message);
  }
}

async function reindexDocument(id) {
  try {
    const document = await api(`/api/documents/${id}/index`, { method: "POST" });
    await refreshDocuments();
    showToast(document.index_status === "indexed" ? "Document indexed." : document.index_error);
  } catch (error) {
    showToast(error.message);
  }
}

async function initializeWorkspace() {
  showSignedIn();
  try {
    await Promise.all([refreshConversations(), refreshDocuments()]);
  } catch (error) {
    if (token()) {
      showToast(error.message);
    }
  }
}

authSwitch.addEventListener("click", () => {
  isRegistering = !isRegistering;
  authSubmit.textContent = isRegistering ? "Create account" : "Sign in";
  authSwitchLabel.textContent = isRegistering ? "Already have an account?" : "New here?";
  authSwitch.textContent = isRegistering ? "Sign in" : "Create an account";
  document.querySelector("#auth-password").autocomplete = isRegistering ? "new-password" : "current-password";
  clearError(authError);
});

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError(authError);
  authSubmit.disabled = true;
  const email = document.querySelector("#auth-email").value.trim().toLowerCase();
  const password = document.querySelector("#auth-password").value;
  try {
    if (isRegistering) {
      await api("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
    }
    const form = new URLSearchParams({ username: email, password });
    const result = await api("/api/auth/login", { method: "POST", body: form });
    localStorage.setItem(AUTH_KEY, result.access_token);
    localStorage.setItem(EMAIL_KEY, email);
    await initializeWorkspace();
  } catch (error) {
    showError(authError, error.message);
  } finally {
    authSubmit.disabled = false;
  }
});

signOutButton.addEventListener("click", signOut);

document.querySelector("#new-conversation").addEventListener("click", () => {
  activeConversationId = null;
  clearChat();
  chatQuestion.focus();
});

documentFile.addEventListener("change", async () => {
  const file = documentFile.files?.[0];
  if (!file) {
    return;
  }
  const data = new FormData();
  data.append("file", file);
  try {
    const document = await api("/api/documents/upload", { method: "POST", body: data });
    await refreshDocuments();
    showToast(
      document.index_status === "indexed"
        ? `${document.filename} uploaded and indexed.`
        : document.index_error || `${document.filename} was uploaded but could not be indexed.`
    );
  } catch (error) {
    showToast(error.message);
  } finally {
    documentFile.value = "";
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError(chatError);
  const question = chatQuestion.value.trim();
  if (!question) {
    showError(chatError, "Enter a research question.");
    return;
  }
  chatSubmit.disabled = true;
  renderMessage({ role: "user", content: question });
  chatQuestion.value = "";
  try {
    const answer = await api("/api/chat/", {
      method: "POST",
      body: JSON.stringify({
        question,
        conversation_id: activeConversationId,
      }),
    });
    activeConversationId = answer.conversation_id;
    renderMessage({ role: "assistant", content: answer.answer, sources: answer.sources });
    await refreshConversations();
  } catch (error) {
    showError(chatError, error.message);
  } finally {
    chatSubmit.disabled = false;
    chatQuestion.focus();
  }
});

if (token()) {
  initializeWorkspace();
} else {
  showSignedOut();
}
