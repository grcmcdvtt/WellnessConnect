document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.toggle-btn');
  
    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('expanded');
    });
  });
  
  function toggleForm() {
    document.getElementById("reminder-form").classList.toggle("hidden");
  }
  
  let lastState = { upcoming: [], inbox: [], completed: [] };
  
  function remindersChanged(newState) {
    return JSON.stringify(newState.upcoming) !== JSON.stringify(lastState.upcoming) ||
          JSON.stringify(newState.inbox) !== JSON.stringify(lastState.inbox) ||
          JSON.stringify(newState.completed) !== JSON.stringify(lastState.completed);
  }
  
  const remindersPerPage = 3;
  const visibleCounts = { upcoming: remindersPerPage, inbox: remindersPerPage, completed: remindersPerPage };
  const hasExpanded = { upcoming: false, inbox: false, completed: false };
  
  function renderReminders(reminders) {
    const upcomingList = document.querySelector("#upcoming");
    const inboxList = document.querySelector("#inbox");
    const completedList = document.querySelector("#completed");
  
    // render upcoming reminders
    if (reminders.upcoming.length) {
      upcomingList.innerHTML = "";
      reminders.upcoming.forEach(r => {
        const li = document.createElement("li");
        li.classList.add("reminder-item");
        li.setAttribute("data-id", r.id);
        li.innerHTML = `
          <div class="reminder-content">
              <div class="reminder-main">
                  <div class="reminder-line">
                    <span class="reminder-time">${r.time}</span>
                    <span class="reminder-text">${r.description}</span>
                  </div>
              </div>
              <div class="actions">
                  <span class="material-symbols-outlined action-toggle" onclick="toggleActionMenu(this)">
                    more_horiz
                  </span>
              <div class="action-menu hidden">
                  <span class="material-symbols-outlined edit" onclick="showEditForm(this)">edit</span>
                  <span class="material-symbols-outlined delete" data-reminder-id="${r.id}" onclick="deleteReminder(this)">delete</span>
              </div>
              </div>
          </div>
          <form class="edit-form hidden" onsubmit="submitEdit(event, this)" data-reminder-id="${r.id}">
              <input type="datetime-local" name="edit_time" required>
              <input type="text" name="edit_description" maxlength="149" required>
              <button type="submit">Save</button>
              <button type="button" onclick="cancelEdit(this)">Cancel</button>
          </form>
        `;
        upcomingList.appendChild(li);
      });
    } else {
      upcomingList.innerHTML = "<li>No upcoming reminders.</li>";
    }
  
    // render inboxed reminders
    if (reminders.inbox.length) {
      inboxList.innerHTML = "";
      reminders.inbox.forEach(r => {
        const li = document.createElement("li");
        li.setAttribute("data-id", r.id);
        li.classList.add("reminder-item");
        li.innerHTML = `
          <div class="reminder-content">
          <div class="circle">
              <span class="material-symbols-outlined check-circle" onclick="toggleComplete(this, ${r.id}, true)">radio_button_unchecked</span>
          </div>
          <div class="reminder-main">
              <div class="reminder-line">
                  <span class="reminder-time">${r.time}</span>
                  <span class="reminder-text">${r.description}</span>
              </div>
          </div>
          <div class="actions">
              <span class="material-symbols-outlined action-toggle" onclick="toggleActionMenu(this)">
              more_horiz
              </span>
              <div class="action-menu hidden">
                  <span class="material-symbols-outlined edit" onclick="showEditForm(this)">edit</span>
                  <span class="material-symbols-outlined delete" data-reminder-id="${r.id}" onclick="deleteReminder(this)">delete</span>
              </div>
          </div>
          </div>
          <form class="edit-form hidden" onsubmit="submitEdit(event, this)" data-reminder-id="${r.id}">
            <input type="datetime-local" name="edit_time" required>
            <input type="text" name="edit_description" maxlength="149" required>
            <button type="submit">Save</button>
            <button type="button" onclick="cancelEdit(this)">Cancel</button>
          </form>
        `;
        inboxList.appendChild(li);
      });
    } else {
      inboxList.innerHTML = "<li>No past reminders.</li>";
    }
  
    // render completed reminders
    if (reminders.completed.length) {
      completedList.innerHTML = ""; // Clear current list
      reminders.completed.forEach(r => {
        const li = document.createElement("li");
        li.classList.add("reminder-item");
        li.setAttribute("data-id", r.id);
        li.innerHTML = `  
          <div class="reminder-content">
          <div class="circle">
              <span class="material-symbols-outlined check-circle" onclick="toggleComplete(this, ${r.id}, false)">check_circle</span>
          </div>
          <div class="reminder-main">
              <div class="reminder-line">
                  <span class="reminder-time">${r.time}</span>
                  <span class="reminder-text">${r.description}</span>
              </div>
          </div>
          <div class="actions">
              <span class="material-symbols-outlined action-toggle" onclick="toggleActionMenu(this)">
              more_horiz
              </span>
              <div class="action-menu hidden">
                  <span class="material-symbols-outlined delete" data-reminder-id="${r.id}" onclick="deleteReminder(this)">delete</span>
              </div>
          </div>
          </div>
        `;
        completedList.appendChild(li);
      });
    } else {
      completedList.innerHTML = "<li>No completed reminders.</li>";
    }
  
    updateReminderVisibility("upcoming");
    updateReminderVisibility("inbox");
    updateReminderVisibility("completed");
  
    lastState = reminders;
  }
  
  function toggleActionMenu(icon) {
    const menu = icon.parentElement.querySelector(".action-menu");
    menu.classList.toggle("hidden");
  }
  
  function toggleComplete(icon, reminderId, markComplete) {
    fetch(`/reminders/complete/${reminderId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_completed: markComplete })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        fetch("/reminders/status")
          .then(res => res.json())
          .then(data => renderReminders(data));
      } else {
        alert("Error updating reminder.");
      }
    });
  }
  
  function toLocalInputValue(datetimeStr) {
    const date = new Date(datetimeStr);
    const offset = date.getTimezoneOffset();
    const localDate = new Date(date.getTime() - offset * 60000);
    return localDate.toISOString().slice(0, 16);
  }
  
  function showEditForm(button) {
      const li = button.closest("li");
      const form = li.querySelector(".edit-form");
      const actionMenu = li.querySelector(".action-menu");
    
      actionMenu.classList.add("hidden");
    
      const timeElem = li.querySelector(".reminder-time");
      const descElem = li.querySelector(".reminder-text");
    
      if (!timeElem || !descElem) return alert("Could not find reminder time or description.");
    
      const datetimeStr = timeElem.textContent.trim();
      const description = descElem.textContent.trim();
    
      form.querySelector("[name='edit_time']").value = toLocalInputValue(datetimeStr);
      form.querySelector("[name='edit_description']").value = description;
    
      form.style.display = "flex";
  }
    
  
  function cancelEdit(button) {
    const li = button.closest("li");
    const form = li.querySelector(".edit-form");
    const actionMenu = li.querySelector(".action-menu");
  
    form.style.display = "none"; // Hide form when canceling edit
    actionMenu.classList.remove("hidden");
  }
  
  function submitEdit(event, form) {
    event.preventDefault();
    const reminderId = form.getAttribute("data-reminder-id");
    const newTime = form.querySelector("[name='edit_time']").value;
    const newDesc = form.querySelector("[name='edit_description']").value;
    
    fetch(`/reminders/edit/${reminderId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_time: newTime, new_description: newDesc })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        fetch("/reminders/status")
          .then(res => res.json())
          .then(data => {
            renderReminders(data);
            form.classList.add("hidden"); // hide the form after saving
          });
      } else {
        alert("Error editing reminder.");
      }
    });
  }
  
  function deleteReminder(buttonEl) {
    const reminderId = buttonEl.getAttribute("data-reminder-id");
  
    fetch(`/reminders/delete/${reminderId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        fetch("/reminders/status")
          .then(res => res.json())
          .then(data => renderReminders(data));
      } else {
        alert("Error deleting reminder.");
      }
    })
    .catch(err => {
      alert("Request error: " + err.message);
    });
  }
  
  function deleteAllCompleted() {
      if (!confirm("Delete all completed reminders?")) return;
    
      fetch('/reminders/delete_completed', {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          fetch("/reminders/status")
            .then(res => res.json())
            .then(data => renderReminders(data)); // Re-render reminders
        } else {
          alert("Error deleting all completed reminders.");
        }
      })
      .catch(err => alert("Error deleting reminders: " + err.message));
    }
    
  
  document.addEventListener("DOMContentLoaded", () => {
      setInterval(() => {
        fetch("/reminders/status")
          .then(res => res.json())
          .then(data => {
            if (remindersChanged(data)) {
              renderReminders(data);
            }
          });
      }, 1000);
  });
  
  document.addEventListener("DOMContentLoaded", () => {
      updateReminderVisibility("upcoming");
      updateReminderVisibility("inbox");
      updateReminderVisibility("completed");
  });
  
  function showMoreReminders(sectionId) {
      const items = document.querySelectorAll(`#${sectionId} .reminder-item`);
      const remaining = items.length - visibleCounts[sectionId];
    
      if (remaining > 0) {
        visibleCounts[sectionId] += Math.min(remindersPerPage, remaining);
        hasExpanded[sectionId] = true;
        updateReminderVisibility(sectionId);
      }
  }
  
  function updateReminderVisibility(sectionId) {
      const items = document.querySelectorAll(`#${sectionId} .reminder-item`);
      const visibleCount = visibleCounts[sectionId];
    
      items.forEach((item, index) => {
        item.style.display = index < visibleCount ? "list-item" : "none";
      });
    
      const showMoreBtn = document.getElementById(`show-more-btn-${sectionId}`);
      const collapseBtn = document.getElementById(`collapse-btn-${sectionId}`);
    
      if (items.length > remindersPerPage) {
        if (visibleCount >= items.length) {
          showMoreBtn.classList.add("hidden");
        } else {
          showMoreBtn.classList.remove("hidden");
        }
        collapseBtn.classList.toggle("hidden", !hasExpanded[sectionId]);
      } else {
        showMoreBtn.classList.add("hidden");
        collapseBtn.classList.add("hidden");
      }
  
      document.getElementById(sectionId).classList.remove("preload-hidden");
  }
  
  function collapseReminders(sectionId) {
      visibleCounts[sectionId] = remindersPerPage;
      hasExpanded[sectionId] = false;
      updateReminderVisibility(sectionId);
  }