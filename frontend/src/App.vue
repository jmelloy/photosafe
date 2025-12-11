<template>
  <div class="app">
    <!-- Show auth screens if not authenticated -->
    <Login
      v-if="!isAuthenticatedRef && currentView === 'login'"
      @login-success="handleLoginSuccess"
      @switch-to-register="currentView = 'register'"
    />
    <Register
      v-else-if="!isAuthenticatedRef && currentView === 'register'"
      @register-success="currentView = 'login'"
      @switch-to-login="currentView = 'login'"
    />

    <!-- Show main app if authenticated -->
    <div v-else>
      <header class="header">
        <div class="header-content">
          <div>
            <h1>📷 PhotoSafe Gallery</h1>
            <p>Your personal photo collection</p>
          </div>
          <div class="user-info">
            <span v-if="currentUser" class="username">{{
              currentUser.username
            }}</span>
            <button @click="handleLogout" class="logout-button">Logout</button>
          </div>
        </div>
      </header>

      <main class="main">
        <aside class="sidebar">
          <div class="sidebar-header">
            <h3>🔍 Filters</h3>
            <button
              v-if="hasActiveFilters"
              @click="clearFilters"
              class="clear-filters-btn"
            >
              Clear All
            </button>
          </div>

          <!-- Search -->
          <div class="filter-section">
            <label class="filter-label">Search</label>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search photos..."
              class="filter-input"
            />
          </div>

          <!-- Albums -->
          <div class="filter-section">
            <label class="filter-label">Album</label>
            <select v-model="selectedAlbum" class="filter-select">
              <option value="">All Albums</option>
              <option v-for="album in albums" :key="album" :value="album">
                {{ album }}
              </option>
            </select>
          </div>

          <!-- Keywords -->
          <div class="filter-section" v-if="keywords.length > 0">
            <label class="filter-label">Keywords</label>
            <select v-model="selectedKeyword" class="filter-select">
              <option value="">All Keywords</option>
              <option v-for="keyword in keywords" :key="keyword" :value="keyword">
                {{ keyword }}
              </option>
            </select>
          </div>

          <!-- People -->
          <div class="filter-section" v-if="persons.length > 0">
            <label class="filter-label">People</label>
            <select v-model="selectedPerson" class="filter-select">
              <option value="">All People</option>
              <option v-for="person in persons" :key="person" :value="person">
                {{ person }}
              </option>
            </select>
          </div>

          <!-- Date Range -->
          <div class="filter-section">
            <label class="filter-label">Date Range</label>
            <input
              v-model="startDate"
              type="date"
              class="filter-input"
              placeholder="Start date"
            />
            <input
              v-model="endDate"
              type="date"
              class="filter-input"
              placeholder="End date"
            />
          </div>

          <!-- Photo Type -->
          <div class="filter-section">
            <label class="filter-label">Photo Type</label>
            <div class="checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="filterFavorites" />
                <span>⭐ Favorites</span>
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="filterPhotos" />
                <span>📷 Photos</span>
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="filterVideos" />
                <span>🎬 Videos</span>
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="filterScreenshots" />
                <span>🖥️ Screenshots</span>
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="filterPanoramas" />
                <span>🏞️ Panoramas</span>
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="filterPortraits" />
                <span>👤 Portraits</span>
              </label>
            </div>
          </div>

          <!-- Location -->
          <div class="filter-section">
            <label class="filter-label">Location</label>
            <label class="checkbox-label">
              <input type="checkbox" v-model="filterHasLocation" />
              <span>📍 Has Location</span>
            </label>
          </div>
        </aside>

        <div class="content">
          <PhotoGallery
            :photos="photos"
            :loading="loading"
            :loading-more="loadingMore"
            :has-more="hasMore"
            @delete-photo="handleDeletePhoto"
            @load-more="loadMorePhotos"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import PhotoGallery from "./components/PhotoGallery.vue";
import Login from "./components/Login.vue";
import Register from "./components/Register.vue";
import { getPhotos, deletePhoto, getAvailableFilters } from "./api/photos";
import { isAuthenticated, getCurrentUser, logout } from "./api/auth";
import type { Photo, User } from "./types/api";
import type { PhotoFilters } from "./api/photos";

const photos = ref<Photo[]>([]);
const loading = ref<boolean>(false);
const loadingMore = ref<boolean>(false);
const currentPage = ref<number>(1);
const hasMore = ref<boolean>(true);
const totalPhotos = ref<number>(0);
const searchQuery = ref<string>("");
const selectedAlbum = ref<string>("");
const selectedKeyword = ref<string>("");
const selectedPerson = ref<string>("");
const startDate = ref<string>("");
const endDate = ref<string>("");
const filterFavorites = ref<boolean>(false);
const filterPhotos = ref<boolean>(false);
const filterVideos = ref<boolean>(false);
const filterScreenshots = ref<boolean>(false);
const filterPanoramas = ref<boolean>(false);
const filterPortraits = ref<boolean>(false);
const filterHasLocation = ref<boolean>(false);
const albums = ref<string[]>([]);
const keywords = ref<string[]>([]);
const persons = ref<string[]>([]);
const currentView = ref<"login" | "register">("login");
const currentUser = ref<User | null>(null);

const buildFilters = (): PhotoFilters => {
  const filters: PhotoFilters = {};
  
  if (searchQuery.value) filters.search = searchQuery.value;
  if (selectedAlbum.value) filters.album = selectedAlbum.value;
  if (selectedKeyword.value) filters.keyword = selectedKeyword.value;
  if (selectedPerson.value) filters.person = selectedPerson.value;
  if (startDate.value) filters.start_date = startDate.value;
  if (endDate.value) filters.end_date = endDate.value;
  if (filterFavorites.value) filters.favorite = true;
  if (filterPhotos.value) filters.isphoto = true;
  if (filterVideos.value) filters.ismovie = true;
  if (filterScreenshots.value) filters.screenshot = true;
  if (filterPanoramas.value) filters.panorama = true;
  if (filterPortraits.value) filters.portrait = true;
  if (filterHasLocation.value) filters.has_location = true;
  
  return filters;
};

const loadPhotos = async (reset: boolean = true) => {
  if (reset) {
    loading.value = true;
    currentPage.value = 1;
    photos.value = [];
  } else {
    loadingMore.value = true;
  }
  
  try {
    const filters = buildFilters();
    const response = await getPhotos(currentPage.value, 50, filters);
    
    if (reset) {
      photos.value = response.items;
    } else {
      photos.value = [...photos.value, ...response.items];
    }
    
    hasMore.value = response.has_more;
    totalPhotos.value = response.total;
  } catch (error: any) {
    console.error("Failed to load photos:", error);
    // If unauthorized, logout and show login screen
    if (error.response?.status === 401) {
      handleLogout();
    } else {
      alert("Failed to load photos. Please try again.");
    }
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
};

const loadAvailableFilters = async () => {
  try {
    const filters = await getAvailableFilters();
    albums.value = filters.albums;
    keywords.value = filters.keywords;
    persons.value = filters.persons;
  } catch (error) {
    console.error("Failed to load filters:", error);
  }
};

const loadMorePhotos = async () => {
  if (!hasMore.value || loadingMore.value) {
    return;
  }
  
  currentPage.value += 1;
  await loadPhotos(false);
};

const loadCurrentUser = async () => {
  try {
    currentUser.value = await getCurrentUser();
  } catch (error) {
    console.error("Failed to load current user:", error);
  }
};

const hasActiveFilters = computed(() => {
  return (
    searchQuery.value ||
    selectedAlbum.value ||
    selectedKeyword.value ||
    selectedPerson.value ||
    startDate.value ||
    endDate.value ||
    filterFavorites.value ||
    filterPhotos.value ||
    filterVideos.value ||
    filterScreenshots.value ||
    filterPanoramas.value ||
    filterPortraits.value ||
    filterHasLocation.value
  );
});

const clearFilters = () => {
  searchQuery.value = "";
  selectedAlbum.value = "";
  selectedKeyword.value = "";
  selectedPerson.value = "";
  startDate.value = "";
  endDate.value = "";
  filterFavorites.value = false;
  filterPhotos.value = false;
  filterVideos.value = false;
  filterScreenshots.value = false;
  filterPanoramas.value = false;
  filterPortraits.value = false;
  filterHasLocation.value = false;
};

// Watch for filter changes and reload photos
watch(
  [
    searchQuery,
    selectedAlbum,
    selectedKeyword,
    selectedPerson,
    startDate,
    endDate,
    filterFavorites,
    filterPhotos,
    filterVideos,
    filterScreenshots,
    filterPanoramas,
    filterPortraits,
    filterHasLocation,
  ],
  () => {
    loadPhotos(true);
  }
);

const handleDeletePhoto = async (photoId: string) => {
  if (confirm("Are you sure you want to delete this photo?")) {
    try {
      await deletePhoto(photoId);
      await loadPhotos();
      // Reload filters to update dropdowns in case deleted photo had unique filter values
      await loadAvailableFilters();
    } catch (error) {
      console.error("Failed to delete photo:", error);
      alert("Failed to delete photo. Please try again.");
    }
  }
};

const handleLoginSuccess = async () => {
  isAuthenticatedRef.value = true;
  await loadCurrentUser();
  await loadAvailableFilters();
  await loadPhotos();
};

const handleLogout = () => {
  logout();
  currentUser.value = null;
  photos.value = [];
  albums.value = [];
  keywords.value = [];
  persons.value = [];
  currentView.value = "login";
  isAuthenticatedRef.value = false;
};

const isAuthenticatedRef = ref<boolean>(isAuthenticated());

onMounted(() => {
  if (isAuthenticatedRef.value) {
    loadCurrentUser();
    loadAvailableFilters();
    loadPhotos();
  }
});
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: #121212;
}

.header {
  background: #1e1e1e;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
  color: #e0e0e0;
}

.header p {
  font-size: 1.2rem;
  opacity: 0.8;
  color: #b0b0b0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.username {
  color: #e0e0e0;
  font-size: 1rem;
  font-weight: 500;
}

.logout-button {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  transition: background 0.2s;
}

.logout-button:hover {
  background: #5568d3;
}

.main {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 2rem;
  align-items: start;
}

@media (max-width: 1024px) {
  .main {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static !important;
  }
}

.sidebar {
  background: #1e1e1e;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  position: sticky;
  top: 2rem;
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #3a3a3a;
}

.sidebar-header h3 {
  margin: 0;
  color: #e0e0e0;
  font-size: 1.2rem;
}

.clear-filters-btn {
  padding: 0.4rem 0.8rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: background 0.2s;
}

.clear-filters-btn:hover {
  background: #5568d3;
}

.filter-section {
  margin-bottom: 1.5rem;
}

.filter-label {
  display: block;
  color: #b0b0b0;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-input,
.filter-select {
  width: 100%;
  padding: 0.65rem;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 0.95rem;
  transition: border-color 0.2s;
  margin-bottom: 0.5rem;
}

.filter-input:focus,
.filter-select:focus {
  outline: none;
  border-color: #667eea;
}

.filter-select option {
  background: #2a2a2a;
  color: #e0e0e0;
}

.filter-input::-webkit-calendar-picker-indicator {
  filter: invert(1);
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: #e0e0e0;
  cursor: pointer;
  font-size: 0.95rem;
  transition: color 0.2s;
}

.checkbox-label:hover {
  color: #667eea;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
  width: 18px;
  height: 18px;
  accent-color: #667eea;
}

.content {
  min-width: 0;
}

/* Sidebar scrollbar styling */
.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.sidebar::-webkit-scrollbar-thumb {
  background: #3a3a3a;
  border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: #4a4a4a;
}
</style>
