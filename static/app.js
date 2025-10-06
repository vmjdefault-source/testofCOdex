const api = {
  token: null,
  async register(data) {
    const response = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error((await response.json()).detail || "Kunde inte registrera");
    }
    return response.json();
  },
  async login(data) {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error((await response.json()).detail || "Fel vid inloggning");
    }
    const payload = await response.json();
    this.token = payload.access_token;
    return payload;
  },
  async upload(formData) {
    const response = await fetch("/documents/upload", {
      method: "POST",
      headers: this._authHeader(),
      body: formData,
    });
    if (!response.ok) {
      throw new Error((await response.json()).detail || "Kunde inte analysera dokumentet");
    }
    return response.json();
  },
  async listDocuments() {
    const response = await fetch("/documents", {
      headers: this._authHeader(),
    });
    if (!response.ok) {
      throw new Error("Kunde inte hämta dokument");
    }
    return response.json();
  },
  async answerQuestion(questionId) {
    const response = await fetch("/questions/answer", {
      method: "POST",
      headers: { ...this._authHeader(), "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: questionId }),
    });
    if (!response.ok) {
      throw new Error((await response.json()).detail || "Kunde inte svara på frågan");
    }
    return response.json();
  },
  _authHeader() {
    if (!this.token) return {};
    return { Authorization: `Bearer ${this.token}` };
  },
};

function show(element) {
  element.classList.remove("hidden");
}

function hide(element) {
  element.classList.add("hidden");
}

function setFeedback(role, message) {
  const el = document.querySelector(`[data-role="${role}"]`);
  if (el) {
    el.textContent = message;
  }
}

async function refreshDocuments() {
  const listSection = document.getElementById("documents-list");
  const list = listSection.querySelector("ul");
  list.innerHTML = "";
  try {
    const documents = await api.listDocuments();
    if (documents.length === 0) {
      hide(listSection);
      return;
    }
    show(listSection);
    documents.forEach((doc) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.textContent = `${doc.title} – ${new Date(doc.created_at).toLocaleString()}`;
      button.addEventListener("click", () => renderDocument(doc));
      item.appendChild(button);
      list.appendChild(item);
    });
  } catch (error) {
    setFeedback("upload-feedback", error.message);
  }
}

let selectedQuestionId = null;

function renderDocument(doc) {
  const detailsSection = document.getElementById("document-details");
  document.getElementById("document-title").textContent = doc.title;
  document.getElementById("document-summary").textContent = doc.summary || "Ingen sammanfattning tillgänglig.";
  const questionsList = document.getElementById("questions-list");
  questionsList.innerHTML = "";

  if (doc.questions.length === 0) {
    const li = document.createElement("li");
    li.textContent = "Inga frågor hittades i dokumentet.";
    questionsList.appendChild(li);
    hide(document.getElementById("answer-section"));
  } else {
    doc.questions.forEach((question) => {
      const li = document.createElement("li");
      const text = document.createElement("p");
      text.textContent = question.text;
      const selectButton = document.createElement("button" );
      selectButton.textContent = "Välj fråga";
      selectButton.addEventListener("click", () => {
        selectedQuestionId = question.id;
        document.getElementById("selected-question").textContent = question.text;
        document.getElementById("answer-result").innerHTML = "";
        show(document.getElementById("answer-section"));
      });
      li.appendChild(text);
      li.appendChild(selectButton);
      questionsList.appendChild(li);
    });
  }

  show(detailsSection);
}

function setupEventListeners() {
  const registerForm = document.getElementById("register-form");
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(registerForm);
    const payload = Object.fromEntries(formData.entries());
    try {
      await api.register(payload);
      setFeedback("register-feedback", "Konto skapat! Du kan nu logga in.");
      registerForm.reset();
    } catch (error) {
      setFeedback("register-feedback", error.message);
    }
  });

  const loginForm = document.getElementById("login-form");
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(loginForm);
    const payload = Object.fromEntries(formData.entries());
    try {
      await api.login(payload);
      setFeedback("login-feedback", "Inloggad!");
      show(document.getElementById("app-section"));
      await refreshDocuments();
    } catch (error) {
      setFeedback("login-feedback", error.message);
    }
  });

  const uploadForm = document.getElementById("upload-form");
  uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(uploadForm);
    try {
      const document = await api.upload(formData);
      setFeedback("upload-feedback", "Dokument analyserat!");
      renderDocument(document);
      await refreshDocuments();
    } catch (error) {
      setFeedback("upload-feedback", error.message);
    }
  });

  document.getElementById("answer-button").addEventListener("click", async () => {
    if (!selectedQuestionId) return;
    const resultContainer = document.getElementById("answer-result");
    resultContainer.textContent = "Genererar svar...";
    try {
      const response = await api.answerQuestion(selectedQuestionId);
      resultContainer.innerHTML = `
        <p><strong>Svar:</strong> ${response.answer}</p>
        ${response.supporting_text ? `<p class="support">Källa i texten: ${response.supporting_text}</p>` : ""}
      `;
    } catch (error) {
      resultContainer.textContent = error.message;
    }
  });
}

setupEventListeners();
