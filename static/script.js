const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chatBox = document.getElementById("chat-box");
const sendBtn = document.getElementById("send-btn");
const welcomeSection = document.querySelector(".welcome-section");
const newChatBtn = document.getElementById("new-chat-btn");
const conversationList = document.getElementById("conversation-list");
const storageWarning = document.getElementById("storage-warning");

const HISTORY_KEY = "vanithraja-chat-history";
const ACTIVE_CHAT_KEY = "vanithraja-active-chat";
let conversations = loadConversations();
let currentConversationId = readActiveConversationId();

renderConversationList();
restoreActiveConversation();

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = input.value.trim();
    if (!message) return;

    hideWelcome();
    addMessage(message, "user");
    input.value = "";

    const reply = addMessage("Thinking...", "bot");
    sendBtn.disabled = true;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message })
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.reply || "Chat request failed");
        }

        reply.textContent = data.reply || "No answer received.";
    } catch (error) {
        reply.textContent = "Error: " + error.message;
    } finally {
        sendBtn.disabled = false;
        updateSavedAssistantReply(reply.textContent);
        scrollChatToLatest();
    }
});

document.querySelectorAll(".suggestion-card").forEach(function (button) {
    button.addEventListener("click", function () {
        input.value = button.dataset.prompt || "";
        form.requestSubmit();
    });
});

newChatBtn.addEventListener("click", function () {
    currentConversationId = createConversationId();
    try {
        localStorage.setItem(ACTIVE_CHAT_KEY, currentConversationId);
    } catch (error) {
        showStorageError(error);
    }

    chatBox.replaceChildren();
    if (welcomeSection) {
        welcomeSection.style.display = "";
        chatBox.appendChild(welcomeSection);
    }
    input.value = "";
    input.focus();
    scrollChatToLatest();
});

function hideWelcome() {
    if (welcomeSection) {
        welcomeSection.style.display = "none";
    }
}

function addMessage(message, sender) {
    const div = document.createElement("div");
    div.className = "message " + sender;
    div.textContent = message;
    chatBox.appendChild(div);
    saveCurrentConversation(message, sender);
    scrollChatToLatest();
    return div;
}

function loadConversations() {
    try {
        const saved = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
        if (!Array.isArray(saved)) return [];

        return saved.filter(function (conversation) {
            return conversation &&
                typeof conversation.id === "string" &&
                typeof conversation.title === "string" &&
                Array.isArray(conversation.messages);
        });
    } catch (error) {
        console.error("Could not load saved chat history:", error);
        return [];
    }
}

function readActiveConversationId() {
    try {
        return localStorage.getItem(ACTIVE_CHAT_KEY) || createConversationId();
    } catch (error) {
        showStorageError(error);
        return createConversationId();
    }
}

function saveCurrentConversation(message, sender) {
    let conversation = conversations.find(function (item) {
        return item.id === currentConversationId;
    });

    if (!conversation) {
        conversation = {
            id: currentConversationId,
            title: sender === "user" ? message : "New chat",
            messages: [],
            updatedAt: Date.now()
        };
        conversations.push(conversation);
    }

    conversation.messages.push({ message, sender });
    if (conversation.title === "New chat" && sender === "user") {
        conversation.title = message;
    }
    conversation.updatedAt = Date.now();

    try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(conversations));
        localStorage.setItem(ACTIVE_CHAT_KEY, currentConversationId);
        storageWarning.hidden = true;
    } catch (error) {
        showStorageError(error);
    }

    renderConversationList();
}

function updateSavedAssistantReply(reply) {
    const conversation = conversations.find(function (item) {
        return item.id === currentConversationId;
    });
    if (!conversation || !conversation.messages.length) return;

    const lastMessage = conversation.messages[conversation.messages.length - 1];
    if (lastMessage.sender !== "bot") return;

    lastMessage.message = reply;
    conversation.updatedAt = Date.now();
    try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(conversations));
        storageWarning.hidden = true;
    } catch (error) {
        showStorageError(error);
    }
    renderConversationList();
}

function restoreActiveConversation() {
    const conversation = conversations.find(function (item) {
        return item.id === currentConversationId;
    });
    if (conversation) openConversation(conversation);
}

function openConversation(conversation) {
    currentConversationId = conversation.id;
    chatBox.replaceChildren();
    if (welcomeSection) welcomeSection.style.display = "none";

    conversation.messages.forEach(function (item) {
        const message = document.createElement("div");
        message.className = "message " + item.sender;
        message.textContent = item.message;
        chatBox.appendChild(message);
    });

    try {
        localStorage.setItem(ACTIVE_CHAT_KEY, currentConversationId);
    } catch (error) {
        showStorageError(error);
    }

    renderConversationList();
    scrollChatToLatest();
}

function renderConversationList() {
    conversationList.replaceChildren();
    conversations
        .slice()
        .sort(function (a, b) {
            return (b.updatedAt || 0) - (a.updatedAt || 0);
        })
        .forEach(function (conversation) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "history-item";
            if (conversation.id === currentConversationId) {
                button.classList.add("active");
            }
            button.textContent = conversation.title;
            button.title = conversation.title;
            button.addEventListener("click", function () {
                openConversation(conversation);
            });
            conversationList.appendChild(button);
        });
}

function createConversationId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
        return window.crypto.randomUUID();
    }
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

function showStorageError(error) {
    console.error("Could not save chat history in this browser:", error);
    if (storageWarning) storageWarning.hidden = false;
}

function scrollChatToLatest() {
    chatBox.scrollTop = chatBox.scrollHeight;
}
