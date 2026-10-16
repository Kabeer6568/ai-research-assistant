const form = document.querySelector("#research-form");
const questionInput = document.querySelector("#research-question");
const inputCount = document.querySelector("#input-count");
const formError = document.querySelector("#form-error");
const results = document.querySelector("#results");
const submittedQuestion = document.querySelector("#submitted-question");
const sourceLinks = document.querySelector("#source-links");
const recentList = document.querySelector("#recent-list");
const recentCount = document.querySelector("#recent-count");
const recentQuestions = [];

const researchIndexes = [
  {
    name: "Google Scholar",
    initials: "GS",
    description: "Articles, theses & citations",
    url: "https://scholar.google.com/scholar",
  },
  {
    name: "arXiv",
    initials: "ar",
    description: "Open-access research papers",
    url: "https://arxiv.org/search/",
  },
  {
    name: "PubMed",
    initials: "PM",
    description: "Biomedical & life sciences",
    url: "https://pubmed.ncbi.nlm.nih.gov/",
  },
];

function showError(message) {
  formError.textContent = message;
  formError.hidden = false;
  questionInput.setAttribute("aria-invalid", "true");
}

function clearError() {
  formError.textContent = "";
  formError.hidden = true;
  questionInput.removeAttribute("aria-invalid");
}

function updateRecentSearches(question) {
  const duplicateIndex = recentQuestions.indexOf(question);
  if (duplicateIndex !== -1) {
    recentQuestions.splice(duplicateIndex, 1);
  }
  recentQuestions.unshift(question);
  recentQuestions.splice(5);

  recentList.replaceChildren();
  recentQuestions.forEach((recentQuestion) => {
    const item = document.createElement("li");
    item.className = "recent-item";

    const button = document.createElement("button");
    button.type = "button";
    button.textContent = recentQuestion;
    button.title = recentQuestion;
    button.addEventListener("click", () => submitQuestion(recentQuestion));

    item.append(button);
    recentList.append(item);
  });

  recentCount.textContent = String(recentQuestions.length);
}

function renderResearchIndexes(question) {
  const query = new URLSearchParams({ q: question }).toString();
  sourceLinks.replaceChildren();

  researchIndexes.forEach((index) => {
    const card = document.createElement("a");
    card.className = "source-card";
    card.href = `${index.url}?${query}`;
    card.target = "_blank";
    card.rel = "noopener noreferrer";

    const logo = document.createElement("span");
    logo.className = "source-logo";
    logo.setAttribute("aria-hidden", "true");
    logo.textContent = index.initials;

    const copy = document.createElement("span");
    copy.className = "source-copy";

    const name = document.createElement("strong");
    name.textContent = index.name;

    const description = document.createElement("span");
    description.textContent = index.description;
    copy.append(name, description);

    const arrow = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    arrow.setAttribute("viewBox", "0 0 16 16");
    arrow.setAttribute("aria-hidden", "true");
    arrow.classList.add("source-arrow");
    const arrowPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
    arrowPath.setAttribute("d", "M5 11 11 5M5 5h6v6");
    arrow.append(arrowPath);

    card.append(logo, copy, arrow);
    sourceLinks.append(card);
  });
}

function submitQuestion(value) {
  const question = value.trim();
  if (!question) {
    showError("Enter a research question to get started.");
    questionInput.focus();
    return;
  }

  clearError();
  questionInput.value = question;
  inputCount.textContent = `${question.length} / 500`;
  submittedQuestion.textContent = question;
  updateRecentSearches(question);
  renderResearchIndexes(question);
  results.hidden = false;
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitQuestion(questionInput.value);
});

questionInput.addEventListener("input", () => {
  inputCount.textContent = `${questionInput.value.length} / 500`;
  if (questionInput.value.trim()) {
    clearError();
  }
});

document.querySelectorAll(".suggestion-chip").forEach((button) => {
  button.addEventListener("click", () => {
    const question = button.dataset.question;
    questionInput.value = question;
    inputCount.textContent = `${question.length} / 500`;
    submitQuestion(question);
  });
});

document.querySelector("#new-search").addEventListener("click", () => {
  questionInput.value = "";
  inputCount.textContent = "0 / 500";
  results.hidden = true;
  clearError();
  questionInput.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

document.querySelector("#edit-question").addEventListener("click", () => {
  questionInput.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
});
