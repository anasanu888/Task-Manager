// script.js

document.addEventListener("DOMContentLoaded", function() {
  const saveBtn = document.getElementById("saveBtn");
  const refreshBtn = document.getElementById("refreshBtn");

  saveBtn && saveBtn.addEventListener("click", async () => {
    const title = document.getElementById("title").value.trim();
    const description = document.getElementById("description").value.trim();
    const tagsRaw = document.getElementById("tags").value.trim();
    const tags = tagsRaw ? tagsRaw.split(",").map(t => t.trim()).filter(Boolean) : [];

    if (!title) {
      alert("Please provide a title.");
      return;
    }

    await fetch("/api/task", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description, tags })
    });
    // close modal and refresh
    const modal = bootstrap.Modal.getInstance(document.getElementById('addModal'));
    modal.hide();
    clearForm();
    loadTasks();
  });

  refreshBtn && refreshBtn.addEventListener("click", loadTasks);

  // initial load
  loadTasks();
});

function clearForm() {
  document.getElementById("title").value = "";
  document.getElementById("description").value = "";
  document.getElementById("tags").value = "";
}

async function loadTasks() {
  const res = await fetch("/api/tasks");
  const grouped = await res.json();
  updateColumn("todo", grouped.todo || []);
  updateColumn("inprogress", grouped.inprogress || []);
  updateColumn("done", grouped.done || []);
  updateCounts();
}

function buildTaskCard(task) {
  const div = document.createElement("div");
  div.className = "task";
  div.draggable = true;
  div.id = `task-${task.id}`;
  div.dataset.id = task.id;

  div.addEventListener("dragstart", dragStart);
  div.addEventListener("dragend", dragEnd);

  const title = document.createElement("div");
  title.className = "title";
  title.textContent = task.title;

  const desc = document.createElement("div");
  desc.className = "meta";
  desc.textContent = task.description || "";

  const idline = document.createElement("div");
  idline.className = "meta mt-2 d-flex justify-content-between align-items-center";

  const left = document.createElement("div");
  left.innerHTML = `<small>#${task.id}</small>`;

  const right = document.createElement("div");
  // tags
  if (task.tags && task.tags.length) {
    task.tags.forEach(t => {
      const span = document.createElement("span");
      span.className = "tag";
      span.textContent = t;
      right.appendChild(span);
    });
  }

  // delete button
  const del = document.createElement("button");
  del.className = "btn btn-sm btn-outline-danger ms-2";
  del.textContent = "Delete";
  del.addEventListener("click", () => deleteTask(task.id));

  right.appendChild(del);

  idline.appendChild(left);
  idline.appendChild(right);

  div.appendChild(title);
  div.appendChild(desc);
  div.appendChild(idline);

  return div;
}

function updateColumn(status, tasks) {
  const container = document.getElementById(`col-${status}`);
  container.innerHTML = "";
  tasks.forEach(t => {
    container.appendChild(buildTaskCard(t));
  });
}

function updateCounts() {
  document.getElementById("count-todo").textContent = document.getElementById("col-todo").children.length || 0;
  document.getElementById("count-inprogress").textContent = document.getElementById("col-inprogress").children.length || 0;
  document.getElementById("count-done").textContent = document.getElementById("col-done").children.length || 0;
}

// Drag & Drop handlers
let draggedId = null;

function dragStart(ev) {
  draggedId = ev.target.dataset.id;
  ev.dataTransfer.effectAllowed = "move";
  ev.target.style.opacity = "0.6";
}

function dragEnd(ev) {
  ev.target.style.opacity = "";
  draggedId = null;
}

function allowDrop(ev) {
  ev.preventDefault();
  const body = ev.currentTarget.querySelector(".column-body");
  body.classList.add("drag-over");
}

function drop(ev) {
  ev.preventDefault();
  const column = ev.currentTarget;
  const status = column.dataset.status;
  const body = ev.currentTarget.querySelector(".column-body");
  body.classList.remove("drag-over");

  if (!draggedId) return;
  // append visually
  const card = document.getElementById(`task-${draggedId}`);
  if (card) {
    body.appendChild(card);
  }

  // send update to server
  fetch("/api/move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: draggedId, status })
  }).then(() => {
    updateCounts();
  }).catch(() => {
    alert("Failed to update task status on server");
    loadTasks(); // rollback on failure
  });
}

async function deleteTask(id) {
  if (!confirm("Delete this task?")) return;
  await fetch("/api/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id })
  });
  loadTasks();
}

