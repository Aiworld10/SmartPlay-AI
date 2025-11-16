let currentTheme = "",
  currentView = "summary",
  currentLikedFilter = "";
let allDetailedData = [],
  currentPage = 1;
const itemsPerPage = 10;

// Theme filter
document.querySelectorAll(".theme-btn").forEach((btn) => {
  btn.addEventListener("click", function () {
    document
      .querySelectorAll(".theme-btn")
      .forEach((b) => b.classList.remove("active"));
    this.classList.add("active");
    currentTheme = this.dataset.theme;
    document.getElementById("theme-badge").textContent = this.textContent;
    currentPage = 1;
    loadData();
  });
});

// View toggle
document.querySelectorAll(".toggle-btn[data-view]").forEach((btn) => {
  btn.addEventListener("click", function () {
    document
      .querySelectorAll(".toggle-btn[data-view]")
      .forEach((b) => b.classList.remove("active"));
    this.classList.add("active");
    currentView = this.dataset.view;
    const likeFilterContainer = document.getElementById(
      "like-filter-container"
    );
    const paginationControls = document.getElementById("pagination-controls");
    if (currentView === "detailed") {
      likeFilterContainer.style.display = "flex";
    } else {
      likeFilterContainer.style.display = "none";
      paginationControls.style.display = "none";
    }
    loadData();
  });
});

// Like filter
document.querySelectorAll(".toggle-btn[data-liked]").forEach((btn) => {
  btn.addEventListener("click", function () {
    document
      .querySelectorAll(".toggle-btn[data-liked]")
      .forEach((b) => b.classList.remove("active"));
    this.classList.add("active");
    currentLikedFilter = this.dataset.liked;
    currentPage = 1;
    loadData();
  });
});

async function loadData() {
  currentView === "summary"
    ? await loadLeaderboard()
    : await loadDetailedView();
}

async function loadLeaderboard() {
  try {
    const url = currentTheme
      ? `/leaderboard?theme=${currentTheme}`
      : "/leaderboard";
    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to load leaderboard");
    displayLeaderboard(await response.json());
  } catch (error) {
    console.error("Error:", error);
    document.getElementById("leaderboard-list").innerHTML = `
            <div class="no-data">
                <i class="fas fa-exclamation-circle fa-3x text-danger mb-3"></i>
                <p>Failed to load leaderboard</p>
            </div>`;
  }
}

async function loadDetailedView() {
  try {
    const url =
      currentLikedFilter !== ""
        ? `/responses/feedback?liked=${currentLikedFilter}`
        : currentTheme
        ? `/leaderboard/details?theme=${currentTheme}`
        : "/leaderboard/details";
    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to load details");
    allDetailedData = (await response.json()).sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    );
    currentPage = 1;
    displayDetailedViewWithPagination();
  } catch (error) {
    console.error("Error:", error);
    document.getElementById("leaderboard-list").innerHTML = `
            <div class="no-data">
                <i class="fas fa-exclamation-circle fa-3x text-danger mb-3"></i>
                <p>Failed to load detailed view</p>
            </div>`;
  }
}

function displayLeaderboard(data) {
  const container = document.getElementById("leaderboard-list");
  if (!data || data.length === 0) {
    container.innerHTML = `
            <div class="no-data">
                <i class="fas fa-users fa-3x text-muted mb-3"></i>
                <p>No players yet. Be the first to play!</p>
            </div>`;
    return;
  }
  container.innerHTML = data
    .map((player, index) => {
      const rank = index + 1;
      const rankClass =
        rank === 1
          ? "rank-1"
          : rank === 2
          ? "rank-2"
          : rank === 3
          ? "rank-3"
          : "rank-other";
      const medal =
        rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : "";
      return `
            <div class="leaderboard-item fade-in" style="animation-delay: ${
              index * 0.05
            }s">
                <div class="player-info">
                    <div class="rank-badge ${rankClass}">${medal || rank}</div>
                    <div>
                        <div class="player-name" onclick="viewPlayerProfile(${
                          player.id
                        })" style="cursor: pointer; color: #007bff;" title="Click to view profile">${
        player.name || "Anonymous"
      }</div>
                        <div class="stats-row">
                            <span><i class="fas fa-gamepad me-1"></i>${
                              player.games_played
                            } games</span>
                            <span><i class="fas fa-chart-line me-1"></i>Avg: ${player.average_score.toFixed(
                              1
                            )}</span>
                        </div>
                    </div>
                </div>
                <div class="player-score">${player.score || 0}</div>
            </div>`;
    })
    .join("");
}

function displayDetailedView(data) {
  const container = document.getElementById("leaderboard-list");
  if (!data || data.length === 0) {
    container.innerHTML = `
            <div class="no-data">
                <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                <p>No responses found for this filter.</p>
            </div>`;
    return;
  }
  container.innerHTML = data
    .map((item, index) => {
      const playerName = item.player_name || `Player ${item.player_id}`;
      const theme = item.theme || "Unknown";
      const questionText = item.question_text || "Question not available";
      let likeStatusHtml = "";
      if (item.liked === true) {
        likeStatusHtml =
          '<span class="badge bg-success ms-2"><i class="fas fa-thumbs-up me-1"></i>Liked</span>';
      } else if (item.liked === false) {
        likeStatusHtml =
          '<span class="badge bg-danger ms-2"><i class="fas fa-thumbs-down me-1"></i>Disliked</span>';
      }
      return `
            <div class="detail-card fade-in" style="animation-delay: ${
              index * 0.02
            }s">
                <div class="detail-header">
                    <div>
                        <span class="player-badge">${playerName}</span>
                        <span class="theme-label ms-2">${theme.toUpperCase()}</span>
                        ${likeStatusHtml}
                    </div>
                    <div class="score-badge">
                        <i class="fas fa-star text-warning me-1"></i>${
                          item.score
                        }
                    </div>
                </div>
                <div class="question-text">
                    <i class="fas fa-question-circle me-2"></i>${questionText}
                </div>
                <div class="response-text">
                    <strong><i class="fas fa-user me-2"></i>Response:</strong>
                    <div class="mt-2">${item.response_text}</div>
                </div>
                ${
                  item.llm_feedback
                    ? `
                    <div class="feedback-text">
                        <strong><i class="fas fa-comment-dots me-2"></i>AI Feedback:</strong>
                        <div class="mt-2">${item.llm_feedback}</div>
                    </div>`
                    : ""
                }
            </div>`;
    })
    .join("");
}

function displayDetailedViewWithPagination() {
  const paginationControls = document.getElementById("pagination-controls");
  if (!allDetailedData || allDetailedData.length === 0) {
    displayDetailedView([]);
    paginationControls.style.display = "none";
    return;
  }
  const totalItems = allDetailedData.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const pageData = allDetailedData.slice(startIndex, endIndex);

  displayDetailedView(pageData);

  paginationControls.style.display = "block";
  document.getElementById("page-start").textContent = startIndex + 1;
  document.getElementById("page-end").textContent = endIndex;
  document.getElementById("total-items").textContent = totalItems;
  document.getElementById("current-page-num").textContent = currentPage;

  document.getElementById("prev-page-btn").disabled = currentPage === 1;
  document.getElementById("next-page-btn").disabled = currentPage >= totalPages;
}

function viewPlayerProfile(playerId) {
  if (!playerId) {
    console.error("Invalid player ID");
    return;
  }
  window.location.href = `/players/id/${playerId}`;
}

// Pagination buttons
document.getElementById("prev-page-btn").addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    displayDetailedViewWithPagination();
    document
      .getElementById("leaderboard-list")
      .scrollIntoView({ behavior: "smooth" });
  }
});

document.getElementById("next-page-btn").addEventListener("click", () => {
  const totalPages = Math.ceil(allDetailedData.length / itemsPerPage);
  if (currentPage < totalPages) {
    currentPage++;
    displayDetailedViewWithPagination();
    document
      .getElementById("leaderboard-list")
      .scrollIntoView({ behavior: "smooth" });
  }
});

// Initialize
loadData();
localStorage.removeItem("gameState");
localStorage.removeItem("resultData");
localStorage.removeItem("nextQuestionData");
