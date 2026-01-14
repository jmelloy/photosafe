<template>
  <main class="main">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h3>🔍 Advanced Search</h3>
        <button v-if="hasActiveFilters" @click="clearFilters" class="clear-filters-btn">
          Clear All
        </button>
      </div>

      <!-- Search Text -->
      <div class="filter-section">
        <label class="filter-label">Search Text</label>
        <input v-model="searchText" type="text" placeholder="Search in titles and descriptions..."
          class="filter-input" />
      </div>

      <!-- Places Multi-Select -->
      <div class="filter-section" v-if="availableFilters.places.length > 0">
        <label class="filter-label">Places ({{ selectedPlaces.length }})</label>
        <div class="multi-select-container">
          <label v-for="place in availableFilters.places" :key="place" class="checkbox-label">
            <input type="checkbox" :value="place" v-model="selectedPlaces" />
            <span>{{ place }}</span>
          </label>
        </div>
      </div>

      <!-- Labels Multi-Select -->
      <div class="filter-section" v-if="availableFilters.labels.length > 0">
        <label class="filter-label">Labels ({{ selectedLabels.length }})</label>
        <div class="multi-select-container">
          <label v-for="label in availableFilters.labels" :key="label" class="checkbox-label">
            <input type="checkbox" :value="label" v-model="selectedLabels" />
            <span>{{ label }}</span>
          </label>
        </div>
      </div>

      <!-- Keywords Multi-Select -->
      <div class="filter-section" v-if="availableFilters.keywords.length > 0">
        <label class="filter-label">Keywords ({{ selectedKeywords.length }})</label>
        <div class="multi-select-container">
          <label v-for="keyword in availableFilters.keywords" :key="keyword" class="checkbox-label">
            <input type="checkbox" :value="keyword" v-model="selectedKeywords" />
            <span>{{ keyword }}</span>
          </label>
        </div>
      </div>

      <!-- People Multi-Select -->
      <div class="filter-section" v-if="availableFilters.persons.length > 0">
        <label class="filter-label">People ({{ selectedPersons.length }})</label>
        <div class="multi-select-container">
          <label v-for="person in availableFilters.persons" :key="person" class="checkbox-label">
            <input type="checkbox" :value="person" v-model="selectedPersons" />
            <span>{{ person }}</span>
          </label>
        </div>
      </div>

      <!-- Albums Multi-Select -->
      <div class="filter-section" v-if="availableFilters.albums.length > 0">
        <label class="filter-label">Albums ({{ selectedAlbums.length }})</label>
        <div class="multi-select-container">
          <label v-for="album in availableFilters.albums" :key="album" class="checkbox-label">
            <input type="checkbox" :value="album" v-model="selectedAlbums" />
            <span>{{ album }}</span>
          </label>
        </div>
      </div>

      <!-- Libraries Multi-Select -->
      <div class="filter-section" v-if="availableFilters.libraries.length > 0">
        <label class="filter-label">Libraries ({{ selectedLibraries.length }})</label>
        <div class="multi-select-container">
          <label v-for="library in availableFilters.libraries" :key="library" class="checkbox-label">
            <input type="checkbox" :value="library" v-model="selectedLibraries" />
            <span>{{ library }}</span>
          </label>
        </div>
      </div>

      <!-- Date Range -->
      <div class="filter-section">
        <label class="filter-label">Date Range</label>
        <input v-model="startDate" type="date" class="filter-input" placeholder="Start date" />
        <input v-model="endDate" type="date" class="filter-input" placeholder="End date" />
      </div>

      <!-- Search Button -->
      <div class="filter-section">
        <button @click="() => performSearch()" class="search-btn">
          Search Photos
        </button>
      </div>
    </aside>

    <div class="content">
      <div v-if="searchPerformed && photos.length === 0 && !loading" class="no-results">
        <p>No photos found matching your search criteria.</p>
      </div>
      <PhotoGallery v-else :photos="photos" :loading="loading" :loading-more="loadingMore" :has-more="hasMore"
        @delete-photo="handleDeletePhoto" @load-more="loadMorePhotos" />
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import PhotoGallery from "../components/PhotoGallery.vue";
import { searchPhotos, getSearchFilters } from "../api/search";
import { deletePhoto } from "../api/photos";
import type { Photo } from "../types/api";
import type { SearchFilters, AvailableSearchFilters } from "../api/search";

const route = useRoute();
const router = useRouter();

const photos = ref<Photo[]>([]);
const loading = ref<boolean>(false);
const loadingMore = ref<boolean>(false);
const currentPage = ref<number>(1);
const hasMore = ref<boolean>(true);
const searchPerformed = ref<boolean>(false);

// Filter states
const searchText = ref<string>("");
const selectedPlaces = ref<string[]>([]);
const selectedLabels = ref<string[]>([]);
const selectedKeywords = ref<string[]>([]);
const selectedPersons = ref<string[]>([]);
const selectedAlbums = ref<string[]>([]);
const selectedLibraries = ref<string[]>([]);
const startDate = ref<string>("");
const endDate = ref<string>("");

// Available filter options
const availableFilters = ref<AvailableSearchFilters>({
  places: [],
  labels: [],
  keywords: [],
  persons: [],
  albums: [],
  libraries: [],
});

// Load filters from URL query params
const loadFiltersFromUrl = () => {
  const query = route.query;
  
  if (query.search_text) searchText.value = query.search_text as string;
  if (query.places) {
    selectedPlaces.value = (query.places as string).split(",").filter(Boolean);
  }
  if (query.labels) {
    selectedLabels.value = (query.labels as string).split(",").filter(Boolean);
  }
  if (query.keywords) {
    selectedKeywords.value = (query.keywords as string).split(",").filter(Boolean);
  }
  if (query.persons) {
    selectedPersons.value = (query.persons as string).split(",").filter(Boolean);
  }
  if (query.albums) {
    selectedAlbums.value = (query.albums as string).split(",").filter(Boolean);
  }
  if (query.libraries) {
    selectedLibraries.value = (query.libraries as string).split(",").filter(Boolean);
  }
  if (query.start_date) startDate.value = query.start_date as string;
  if (query.end_date) endDate.value = query.end_date as string;
};

// Update URL with current filter values
const updateUrlParams = () => {
  const query: Record<string, string> = {};
  
  if (searchText.value) query.search_text = searchText.value;
  if (selectedPlaces.value.length > 0) query.places = selectedPlaces.value.join(",");
  if (selectedLabels.value.length > 0) query.labels = selectedLabels.value.join(",");
  if (selectedKeywords.value.length > 0) query.keywords = selectedKeywords.value.join(",");
  if (selectedPersons.value.length > 0) query.persons = selectedPersons.value.join(",");
  if (selectedAlbums.value.length > 0) query.albums = selectedAlbums.value.join(",");
  if (selectedLibraries.value.length > 0) query.libraries = selectedLibraries.value.join(",");
  if (startDate.value) query.start_date = startDate.value;
  if (endDate.value) query.end_date = endDate.value;
  
  // Update URL without reloading the page
  router.replace({ query });
};

const buildFilters = (): SearchFilters => {
  const filters: SearchFilters = {};

  if (searchText.value) filters.search_text = searchText.value;
  if (selectedPlaces.value.length > 0) filters.places = selectedPlaces.value;
  if (selectedLabels.value.length > 0) filters.labels = selectedLabels.value;
  if (selectedKeywords.value.length > 0) filters.keywords = selectedKeywords.value;
  if (selectedPersons.value.length > 0) filters.persons = selectedPersons.value;
  if (selectedAlbums.value.length > 0) filters.albums = selectedAlbums.value;
  if (selectedLibraries.value.length > 0) filters.libraries = selectedLibraries.value;
  if (startDate.value) filters.start_date = startDate.value;
  if (endDate.value) filters.end_date = endDate.value;

  return filters;
};

const performSearch = async (reset: boolean = true) => {
  if (reset) {
    loading.value = true;
    currentPage.value = 1;
    photos.value = [];
  } else {
    loadingMore.value = true;
  }

  try {
    const filters = buildFilters();
    const response = await searchPhotos(currentPage.value, 50, filters);

    if (reset) {
      photos.value = response.items;
      searchPerformed.value = true;
    } else {
      photos.value = [...photos.value, ...response.items];
    }

    hasMore.value = response.has_more;
    
    // Update URL with current filter values
    updateUrlParams();
  } catch (error: unknown) {
    console.error("Failed to search photos:", error);
    alert("Failed to search photos. Please try again.");
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
};

const loadAvailableFilters = async () => {
  try {
    availableFilters.value = await getSearchFilters();
  } catch (error) {
    console.error("Failed to load search filters:", error);
  }
};

const loadMorePhotos = async () => {
  if (!hasMore.value || loadingMore.value) {
    return;
  }

  currentPage.value += 1;
  await performSearch(false);
};

const hasActiveFilters = computed(() => {
  return (
    searchText.value ||
    selectedPlaces.value.length > 0 ||
    selectedLabels.value.length > 0 ||
    selectedKeywords.value.length > 0 ||
    selectedPersons.value.length > 0 ||
    selectedAlbums.value.length > 0 ||
    selectedLibraries.value.length > 0 ||
    startDate.value ||
    endDate.value
  );
});

const clearFilters = () => {
  searchText.value = "";
  selectedPlaces.value = [];
  selectedLabels.value = [];
  selectedKeywords.value = [];
  selectedPersons.value = [];
  selectedAlbums.value = [];
  selectedLibraries.value = [];
  startDate.value = "";
  endDate.value = "";
  photos.value = [];
  searchPerformed.value = false;
  
  // Clear URL params
  router.replace({ query: {} });
};

const handleDeletePhoto = async (photoId: string) => {
  if (confirm("Are you sure you want to delete this photo?")) {
    try {
      await deletePhoto(photoId);
      await performSearch();
      await loadAvailableFilters();
    } catch (error) {
      console.error("Failed to delete photo:", error);
      alert("Failed to delete photo. Please try again.");
    }
  }
};

onMounted(() => {
  loadAvailableFilters();
  // Load filters from URL and perform search if any filters are present
  loadFiltersFromUrl();
  if (hasActiveFilters.value) {
    performSearch();
  }
});
</script>

<style scoped>
.main {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  display: grid;
  grid-template-columns: 320px 1fr;
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

.filter-input {
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

.filter-input:focus {
  outline: none;
  border-color: #667eea;
}

.filter-input::-webkit-calendar-picker-indicator {
  filter: invert(1);
}

.multi-select-container {
  max-height: 200px;
  overflow-y: auto;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 6px;
  padding: 0.5rem;
}

.multi-select-container::-webkit-scrollbar {
  width: 6px;
}

.multi-select-container::-webkit-scrollbar-track {
  background: #2a2a2a;
}

.multi-select-container::-webkit-scrollbar-thumb {
  background: #4a4a4a;
  border-radius: 3px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: #e0e0e0;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.4rem 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.checkbox-label:hover {
  background: #3a3a3a;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
  accent-color: #667eea;
}

.search-btn {
  width: 100%;
  padding: 0.8rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
}

.search-btn:active {
  transform: translateY(0);
}

.content {
  min-width: 0;
}

.no-results {
  text-align: center;
  padding: 3rem;
  color: #b0b0b0;
  font-size: 1.1rem;
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
