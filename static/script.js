async function fetchData() {
    loadClassrooms();
    loadSubjects();
    loadTimetable();
}

// ---------- CLASSROOM ----------
async function addClassroom() {
    let name = document.getElementById("classroomName").value;

    await fetch("/api/classrooms", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name})
    });

    loadClassrooms();
}

async function loadClassrooms() {
    let res = await fetch("/api/classrooms");
    let data = await res.json();

    let select = document.getElementById("classroomSelect");
    select.innerHTML = "";

    data.forEach(c => {
        select.innerHTML += `<option value="${c.id}">${c.name}</option>`;
    });
}


// ---------- SUBJECT ----------
async function addSubject() {
    let name = document.getElementById("subjectName").value;

    await fetch("/api/subjects", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name})
    });

    loadSubjects();
}

async function loadSubjects() {
    let res = await fetch("/api/subjects");
    let data = await res.json();

    let select = document.getElementById("subjectSelect");
    select.innerHTML = "";

    data.forEach(s => {
        select.innerHTML += `<option value="${s.id}">${s.name}</option>`;
    });
}


// ---------- TIMETABLE ----------
async function addTimetable() {
    let classroom_id = document.getElementById("classroomSelect").value;
    let subject_id = document.getElementById("subjectSelect").value;
    let day = document.getElementById("day").value;
    let time = document.getElementById("time").value;

    let res = await fetch("/api/timetable", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({classroom_id, subject_id, day, time})
    });

    let data = await res.json();

    if (data.error) {
        alert(data.error);
    }

    loadTimetable();
}

async function loadTimetable() {
    let res = await fetch("/api/timetable");
    let data = await res.json();

    let list = document.getElementById("timetableList");
    list.innerHTML = "";

    data.forEach(t => {
        list.innerHTML += `<li>${t.classroom} - ${t.subject} - ${t.day} - ${t.time}</li>`;
    });
}

// DELETE TIMETABLE
async function deleteTimetable(id) {
    await fetch(`/api/timetable/${id}`, {
        method: "DELETE"
    });
    loadTable();
}

// EDIT TIMETABLE
function editTimetable(t) {
    document.getElementById("classroomSelect").value = t.classroom_id;
    document.getElementById("subjectSelect").value = t.subject_id;
    document.getElementById("day").value = t.day;
    document.getElementById("time").value = t.time;

    window.editId = t.id;
}

// MODIFY ADD FUNCTION
async function addTimetable() {
    let classroom_id = document.getElementById("classroomSelect").value;
    let subject_id = document.getElementById("subjectSelect").value;
    let day = document.getElementById("day").value;
    let time = document.getElementById("time").value;

    let method = "POST";
    let url = "/api/timetable";

    if (window.editId) {
        method = "PUT";
        url = `/api/timetable/${window.editId}`;
    }

    await fetch(url, {
        method: method,
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({classroom_id, subject_id, day, time})
    });

    window.editId = null;
    loadTable();
}

async function generateAI() {

    let classroom_id = document.getElementById("aiClassroom").value;

    let days = document.getElementById("days").value.split(",");
    let times = document.getElementById("times").value.split(",");
    let subjects = document.getElementById("subjectsAI").value.split(",");

    let res = await fetch("/api/auto_schedule", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            classroom_id,
            days,
            times,
            subjects
        })
    });

    let data = await res.json();
    alert(data.message);
}


async function loadClassrooms() {
    let res = await fetch("/api/classrooms");
    let data = await res.json();

    let select = document.getElementById("classroomSelect");
    let aiSelect = document.getElementById("aiClassroom");

    if (select) select.innerHTML = "";
    if (aiSelect) aiSelect.innerHTML = "";

    data.forEach(c => {
        let option = `<option value="${c.id}">${c.name}</option>`;

        if (select) select.innerHTML += option;
        if (aiSelect) aiSelect.innerHTML += option;
    });
}

async function loadSubjectsCheckbox() {
    let res = await fetch("/api/subjects");
    let data = await res.json();

    let box = document.getElementById("subjectCheckboxes");
    if (!box) return;

    box.innerHTML = "";

    data.forEach(s => {
        box.innerHTML += `
        <label>
            <input type="checkbox" value="${s.id}">
            ${s.name}
        </label>`;
    });
}

async function generateAI() {

    let classroom_id = document.getElementById("aiClassroom").value;

    let days = document.getElementById("days").value.split(",");
    let times = document.getElementById("times").value.split(",");

    // ✅ FIX: convert to number
    let selected = [];
    document.querySelectorAll("#subjectCheckboxes input:checked")
        .forEach(cb => selected.push(parseInt(cb.value)));

    if (selected.length === 0) {
        alert("Select at least one subject");
        return;
    }

    let res = await fetch("/api/auto_schedule", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            classroom_id: parseInt(classroom_id),
            days,
            times,
            subjects: selected
        })
    });

    let data = await res.json();
    alert(data.message);

    // ✅ REFRESH DATA
    loadTimetable();
}

async function loadSubjectsCheckbox() {
    let res = await fetch("/api/subjects");
    let data = await res.json();

    let box = document.getElementById("subjectCheckboxes");

    if (!box) return;  // important

    box.innerHTML = "";

    data.forEach(s => {
        box.innerHTML += `
        <label>
            <input type="checkbox" value="${s.id}">
            ${s.name}
        </label>`;
    });
}

async function clearTimetable() {
    await fetch("/api/clear_timetable", {method: "POST"});
    alert("Cleared!");
}

async function clearData() {

    let confirmDelete = confirm("⚠️ Clear all timetable data?");
    if (!confirmDelete) return;

    // 🔥 delete from database
    await fetch("/api/delete_all", { method: "POST" });

    // ✅ RESET SUBJECT CHECKBOXES
    document.querySelectorAll("#subjectCheckboxes input")
        .forEach(cb => cb.checked = false);

    // ✅ CLEAR INPUT FIELDS
    document.getElementById("days").value = "";
    document.getElementById("times").value = "";

    // ✅ RESET DROPDOWN (optional)
    let select = document.getElementById("aiClassroom");
    if (select) select.selectedIndex = 0;

    alert("✅ Cleared & Reset!");

    // optional: refresh table
    if (typeof loadTable === "function") loadTable();

    document.getElementById("day").value = "";
    document.getElementById("time").value = "";
}

async function autoGenerate() {
    let res = await fetch("/api/auto_generate", {
        method: "POST"
    });

    let data = await res.json();

    alert(data.message);

    // refresh timetable
    if (typeof loadTable === "function") loadTable();
}

window.onload = function () {
    loadClassrooms();
    loadSubjects();
    loadSubjectsCheckbox();   // ✅ ADD THIS
}


fetchData();