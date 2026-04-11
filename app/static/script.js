const stepLibrary = {
  incoming: {
    title: "Incoming call",
    description: "+31 6 12312345",
    className: "flow-node--incoming",
    icon: "📞",
  },
  tts: {
    title: "Text-to-speech",
    description: "Generated voice message for caller",
    className: "flow-node--tts",
    icon: "🔊",
  },
  sound: {
    title: "Play Sound File",
    description: "Custom audio file playback",
    className: "flow-node--sound",
    icon: "🎵",
  },
  if: {
    title: "If",
    description: "If the caller presses a button → Then ...",
    className: "flow-node--if",
    icon: "↳",
  },
  forward: {
    title: "Forward Call",
    description: "Route the call to another number",
    className: "flow-node--forward",
    icon: "📲",
  },
  record: {
    title: "Record Call Audio",
    description: "Save voice message from caller",
    className: "flow-node--record",
    icon: "⏺",
  },
  url: {
    title: "Fetch call flow from URL",
    description: "Load external flow by URL",
    className: "flow-node--url",
    icon: "🔗",
  },
  pause: {
    title: "Pause",
    description: "Wait 10 seconds before next step",
    className: "flow-node--pause",
    icon: "⏸",
  },
  end: {
    title: "End Call",
    description: "Finish call scenario",
    className: "flow-node--end",
    icon: "☎",
  },
};

const state = {
  flow_name: "Call Center",
  is_published: false,
  steps: [],
};

const dynamicList = document.getElementById("dynamicList");
const stepPalette = document.getElementById("stepPalette");
const saveBtn = document.getElementById("saveBtn");
const resetBtn = document.getElementById("resetBtn");
const publishBtn = document.getElementById("publishBtn");
const renameBtn = document.getElementById("renameBtn");
const dropZone = document.getElementById("dropZone");
const toast = document.getElementById("toast");
const flowNameElement = document.getElementById("flowName");
const publishStatusElement = document.getElementById("publishStatus");

function generateId(prefix = "step") {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("toast--visible");

  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => {
    toast.classList.remove("toast--visible");
  }, 2200);
}

function getStepView(step) {
  const fallback = {
    className: "flow-node--tts",
    icon: "•",
  };

  return stepLibrary[step.type] || fallback;
}

function updateHeader() {
  flowNameElement.textContent = state.flow_name;
  publishStatusElement.textContent = state.is_published ? "Published" : "Draft";
  publishStatusElement.classList.toggle("status-pill--published", state.is_published);
}

function renderFlow() {
  dynamicList.innerHTML = "";

  state.steps.forEach((step, index) => {
    const view = getStepView(step);
    const segment = document.createElement("div");
    segment.className = "flow-segment";

    const connectorTop = index === 0 ? "" : '<div class="connector"></div>';

    segment.innerHTML = `
      ${connectorTop}
      <div class="flow-node ${view.className}">
        <div class="flow-node__icon">${view.icon}</div>
        <div class="flow-node__content">
          <strong>${step.title}</strong>
          <span>${step.description}</span>
        </div>
        <div class="node-actions">
          <button class="icon-btn move-up-btn" title="Поднять выше">↑</button>
          <button class="icon-btn remove-btn" title="Удалить">×</button>
        </div>
      </div>
    `;

    const removeBtn = segment.querySelector(".remove-btn");
    const moveUpBtn = segment.querySelector(".move-up-btn");

    removeBtn.addEventListener("click", () => {
      state.steps = state.steps.filter((item) => item.id !== step.id);
      state.is_published = false;
      renderFlow();
      updateHeader();
    });

    moveUpBtn.addEventListener("click", () => {
      const currentIndex = state.steps.findIndex((item) => item.id === step.id);
      if (currentIndex > 0) {
        [state.steps[currentIndex - 1], state.steps[currentIndex]] = [state.steps[currentIndex], state.steps[currentIndex - 1]];
        state.is_published = false;
        renderFlow();
        updateHeader();
      }
    });

    dynamicList.appendChild(segment);
  });
}

async function loadFlow() {
  const response = await fetch("/api/flow");
  const data = await response.json();

  state.flow_name = data.flow_name;
  state.is_published = data.is_published;
  state.steps = data.steps;

  updateHeader();
  renderFlow();
}

function createStepByType(type) {
  const config = stepLibrary[type];
  if (!config) return null;

  return {
    id: generateId(type),
    type,
    title: config.title,
    description: config.description,
  };
}

stepPalette.addEventListener("click", (event) => {
  const button = event.target.closest(".step-item");
  if (!button) return;

  const newStep = createStepByType(button.dataset.type);
  if (!newStep) return;

  state.steps.push(newStep);
  state.is_published = false;
  renderFlow();
  updateHeader();
});

dropZone.addEventListener("click", () => {
  const newStep = createStepByType("tts");
  state.steps.push(newStep);
  state.is_published = false;
  renderFlow();
  updateHeader();
});

saveBtn.addEventListener("click", async () => {
  const response = await fetch("/api/flow", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(state),
  });

  if (!response.ok) {
    showToast("Ошибка при сохранении");
    return;
  }

  const data = await response.json();
  state.flow_name = data.flow_name;
  state.is_published = data.is_published;
  state.steps = data.steps;

  updateHeader();
  renderFlow();
  showToast("Сценарий сохранен");
});

resetBtn.addEventListener("click", async () => {
  const response = await fetch("/api/flow/reset", {
    method: "POST",
  });

  if (!response.ok) {
    showToast("Ошибка при сбросе");
    return;
  }

  const data = await response.json();
  state.flow_name = data.flow_name;
  state.is_published = data.is_published;
  state.steps = data.steps;

  updateHeader();
  renderFlow();
  showToast("Сценарий сброшен");
});

publishBtn.addEventListener("click", async () => {
  const saveResponse = await fetch("/api/flow", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(state),
  });

  if (!saveResponse.ok) {
    showToast("Ошибка при сохранении перед публикацией");
    return;
  }

  const publishResponse = await fetch("/api/flow/publish", {
    method: "POST",
  });

  if (!publishResponse.ok) {
    showToast("Ошибка публикации");
    return;
  }

  const data = await publishResponse.json();
  state.flow_name = data.flow_name;
  state.is_published = data.is_published;
  state.steps = data.steps;

  updateHeader();
  renderFlow();
  showToast("Сценарий опубликован");
});

renameBtn.addEventListener("click", () => {
  const newName = prompt("Введите новое название сценария:", state.flow_name);
  if (!newName) return;

  state.flow_name = newName.trim() || state.flow_name;
  state.is_published = false;
  updateHeader();
});

loadFlow().catch((error) => {
  console.error(error);
  showToast("Не удалось загрузить сценарий");
});
