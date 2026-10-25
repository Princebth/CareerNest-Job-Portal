
const API = "/api";
const $ = (id) => document.getElementById(id);

let token = localStorage.getItem("careernest_token") || "";
let currentUser = JSON.parse(
  localStorage.getItem("careernest_user") || "null"
);

let authMode = "login";
let jobsCache = [];
let pendingApplicationJobId = null;

// Escape HTML before displaying user-provided data.
function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

// Common API request function.
async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const isFormData = options.body instanceof FormData;

  if (options.body && !isFormData) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(API + path, {
    ...options,
    headers
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    let errorMessage = `Request failed (${response.status})`;

    if (typeof data.detail === "string") {
      errorMessage = data.detail;
    } else if (Array.isArray(data.detail)) {
      errorMessage = data.detail
        .map((item) => item.msg || "Invalid input")
        .join(", ");
    }

    throw new Error(errorMessage);
  }

  return data;
}

// Toast notification.
function toast(message) {
  const node = $("toast");
  if (!node) return;

  node.textContent = message;
  node.classList.remove("hidden");

  setTimeout(() => {
    node.classList.add("hidden");
  }, 3200);
}

// Login/logout button visibility.
function syncAuth() {
  if ($("login-open")) {
    $("login-open").classList.toggle("hidden", !!currentUser);
  }

  if ($("register-open")) {
    $("register-open").classList.toggle("hidden", !!currentUser);
  }

  if ($("logout")) {
    $("logout").classList.toggle("hidden", !currentUser);
  }

  if ($("post-job-open")) {
    $("post-job-open").textContent =
      currentUser?.role === "recruiter"
        ? "Post a job ↗"
        : "Sign in as recruiter ↗";
  }
}

// Modal helpers.
function openModal(id) {
  $(id)?.classList.remove("hidden");
}

function closeModal(id) {
  $(id)?.classList.add("hidden");
}

// Login and registration mode.
function setAuthMode(mode) {
  authMode = mode;

  if ($("auth-title")) {
    $("auth-title").textContent =
      mode === "login" ? "Log in" : "Create your account";
  }

  if ($("auth-submit")) {
    $("auth-submit").textContent =
      mode === "login" ? "Log in" : "Create account";
  }

  if ($("name-wrap")) {
    $("name-wrap").classList.toggle("hidden", mode === "login");
  }

  if ($("role-wrap")) {
    $("role-wrap").classList.toggle("hidden", mode === "login");
  }

  if ($("auth-name")) {
    $("auth-name").required = mode === "register";
  }

  if ($("switch-auth")) {
    $("switch-auth").innerHTML =
      mode === "login"
        ? 'New here? <button type="button" class="text-button" id="switch-auth-button">Create an account</button>'
        : 'Already registered? <button type="button" class="text-button" id="switch-auth-button">Log in</button>';

    $("switch-auth-button").onclick = () => {
      setAuthMode(authMode === "login" ? "register" : "login");
    };
  }

  if ($("auth-message")) {
    $("auth-message").textContent = "";
  }
}

// Load jobs from the backend.
async function loadJobs() {
  const grid = $("jobs-grid");
  if (!grid) return;

  grid.innerHTML =
    '<div class="empty">Finding opportunities...</div>';

  const params = new URLSearchParams();

  if ($("search")?.value.trim()) {
    params.set("search", $("search").value.trim());
  }

  if ($("location")?.value.trim()) {
    params.set("location", $("location").value.trim());
  }

  if ($("job-type")?.value) {
    params.set("job_type", $("job-type").value);
  }

  try {
    const jobs = await request("/jobs?" + params.toString());
    jobsCache = jobs;

    if (!jobs.length) {
      grid.innerHTML =
        '<div class="empty">No jobs found. Try a different search.</div>';
      return;
    }

    grid.innerHTML = jobs.map((job) => `
      <article class="job-card">
        <div class="job-company">${escapeHtml(job.company)}</div>

        <h3>${escapeHtml(job.title)}</h3>

        <div class="job-meta">
          <span class="chip">⌖ ${escapeHtml(job.location)}</span>
          <span class="chip">${escapeHtml(job.job_type)}</span>
        </div>

        <p class="job-description">
          ${escapeHtml(job.description)}
        </p>

        <div class="job-bottom">
          <span class="salary">
            ${escapeHtml(job.salary || "Salary not listed")}
          </span>

          <button
            type="button"
            class="btn btn-primary apply-button"
            data-id="${Number(job.id)}">
            Apply ↗
          </button>
        </div>
      </article>
    `).join("");

    grid.querySelectorAll(".apply-button").forEach((button) => {
      button.addEventListener("click", () => {
        applyToJob(Number(button.dataset.id));
      });
    });
  } catch (error) {
    grid.innerHTML = `
      <div class="empty">
        Could not load jobs: ${escapeHtml(error.message)}.
        Check the backend server and MySQL connection.
      </div>
    `;
  }
}

// Open the separate application page.
function applyToJob(jobId) {
  if (!currentUser) {
    pendingApplicationJobId = jobId;
    setAuthMode("login");
    openModal("auth-modal");
    toast("Log in with a candidate account to apply.");
    return;
  }

  if (currentUser.role !== "candidate") {
    toast("Recruiter accounts cannot apply for jobs.");
    return;
  }

  const homePage = $("home-page");
  const applicationPage = $("application-page");
  const form = $("application-form");

  if (!homePage || !applicationPage || !form) {
    toast("Application page is missing. Check index.html.");
    return;
  }

  const job = jobsCache.find(
    (item) => Number(item.id) === Number(jobId)
  );

  form.reset();

  if ($("application-job-id")) {
    $("application-job-id").value = jobId;
  }

  $("app-full-name").value = currentUser.name || "";
  $("app-email").value = currentUser.email || "";
  $("application-message").textContent = "";

  if ($("application-job-details")) {
    $("application-job-details").textContent = job
      ? `${job.title} at ${job.company} · ${job.location}`
      : `Job ID: ${jobId}`;
  }

  homePage.hidden = true;
  applicationPage.hidden = false;

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Return to the jobs page.
function returnToJobs() {
  if ($("application-page")) {
    $("application-page").hidden = true;
  }

  if ($("home-page")) {
    $("home-page").hidden = false;
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

$("back-to-jobs")?.addEventListener("click", returnToJobs);

// Submit the application and PDF resume.
$("application-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!currentUser || currentUser.role !== "candidate") {
    toast("Please log in with a candidate account.");
    return;
  }

  const form = $("application-form");
  const message = $("application-message");
  const submitButton = $("submit-application");
  const resume = $("app-resume").files[0];
  const jobId = $("application-job-id")?.value;

  message.textContent = "";

  if (!jobId) {
    message.textContent = "Please select a valid job.";
    return;
  }

  if (!resume) {
    message.textContent = "Please select your resume PDF.";
    return;
  }

  if (
    resume.type !== "application/pdf" &&
    !resume.name.toLowerCase().endsWith(".pdf")
  ) {
    message.textContent = "Please upload a PDF file only.";
    return;
  }

  if (resume.size > 5 * 1024 * 1024) {
    message.textContent = "Resume must be 5 MB or smaller.";
    return;
  }

  const formData = new FormData();

  formData.append("full_name", $("app-full-name").value.trim());
  formData.append("email", $("app-email").value.trim());
  formData.append("phone", $("app-phone").value.trim());
  formData.append("education", $("app-education").value.trim());
  formData.append("college", $("app-college").value.trim());
  formData.append("skills", $("app-skills").value.trim());
  formData.append("experience_level", $("app-experience").value);
  formData.append("resume", resume);
  formData.append(
    "cover_letter",
    $("app-cover-letter").value.trim()
  );

  submitButton.disabled = true;
  submitButton.textContent = "Submitting...";
  message.textContent = "Submitting your application...";

  try {
    await request(`/jobs/${encodeURIComponent(jobId)}/apply`, {
      method: "POST",
      body: formData
    });

    form.reset();
    returnToJobs();
    toast("Application submitted successfully!");
  } catch (error) {
    message.textContent = error.message;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Submit Application";
  }
});

// Open login and registration forms.
$("login-open")?.addEventListener("click", () => {
  setAuthMode("login");
  openModal("auth-modal");
});

$("register-open")?.addEventListener("click", () => {
  setAuthMode("register");
  openModal("auth-modal");
});

// Job search.
$("search-button")?.addEventListener("click", loadJobs);

$("search")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") loadJobs();
});

$("location")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") loadJobs();
});

$("job-type")?.addEventListener("change", loadJobs);

// Logout.
$("logout")?.addEventListener("click", () => {
  token = "";
  currentUser = null;
  pendingApplicationJobId = null;

  localStorage.removeItem("careernest_token");
  localStorage.removeItem("careernest_user");

  syncAuth();
  returnToJobs();
  toast("You have logged out.");
});

// Login and registration submission.
$("auth-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = $("auth-message");
  const submitButton = $("auth-submit");

  message.textContent = "Please wait...";
  submitButton.disabled = true;

  try {
    if (authMode === "register") {
      await request("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          name: $("auth-name").value.trim(),
          email: $("auth-email").value.trim(),
          password: $("auth-password").value,
          role: $("auth-role").value
        })
      });
    }

    const result = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: $("auth-email").value.trim(),
        password: $("auth-password").value
      })
    });

    token = result.access_token;
    currentUser = result.user;

    localStorage.setItem("careernest_token", token);
    localStorage.setItem(
      "careernest_user",
      JSON.stringify(currentUser)
    );

    syncAuth();
    closeModal("auth-modal");
    toast(`Welcome, ${currentUser.name}!`);

    // Continue with the job the candidate originally selected.
    if (pendingApplicationJobId !== null) {
      const jobId = pendingApplicationJobId;
      pendingApplicationJobId = null;
      applyToJob(jobId);
    }
  } catch (error) {
    message.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
});

// Recruiter: open job posting form.
$("post-job-open")?.addEventListener("click", () => {
  if (!currentUser) {
    setAuthMode("login");
    openModal("auth-modal");
    toast("Log in with a recruiter account to post jobs.");
    return;
  }

  if (currentUser.role !== "recruiter") {
    toast("Only recruiter accounts can post jobs.");
    return;
  }

  $("job-message").textContent = "";
  openModal("job-modal");
});

// Recruiter: publish a job.
$("job-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = $("job-message");
  const submitButton = $("job-form").querySelector(
    'button[type="submit"]'
  );

  message.textContent = "Publishing...";
  submitButton.disabled = true;

  try {
    await request("/jobs", {
      method: "POST",
      body: JSON.stringify({
        title: $("job-title").value.trim(),
        company: $("job-company").value.trim(),
        location: $("job-location").value.trim(),
        job_type: $("job-kind").value,
        salary: $("job-salary").value.trim() || null,
        description: $("job-description").value.trim()
      })
    });

    closeModal("job-modal");
    $("job-form").reset();
    $("job-location").value = "Remote";

    toast("Job published successfully!");
    await loadJobs();
  } catch (error) {
    message.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
});

// Modal close buttons.
document.querySelectorAll("[data-close]").forEach((button) => {
  button.addEventListener("click", () => {
    closeModal(button.dataset.close);
  });
});

// Close a modal by clicking its backdrop.
document.querySelectorAll(".modal").forEach((modal) => {
  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeModal(modal.id);
    }
  });
});

// Escape closes open modals.
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.querySelectorAll(".modal").forEach((modal) => {
      modal.classList.add("hidden");
    });
  }
});

// Initial setup.
syncAuth();
setAuthMode("login");
loadJobs();
