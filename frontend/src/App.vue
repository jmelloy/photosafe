<template>
  <div class="app">
    <header class="header">
      <h1>📷 PhotoSafe Gallery</h1>
      <p>Your personal photo collection</p>
    </header>
    
    <main class="main">
      <div class="filters">
        <div class="search-container">
          <input 
            v-model="searchQuery"
            type="text"
            placeholder="Search photos..."
            class="search-input"
          />
        </div>
        
        <div class="filter-group">
          <select v-model="selectedAlbum" class="filter-select">
            <option value="">All Albums</option>
            <option v-for="album in albums" :key="album" :value="album">{{ album }}</option>
          </select>
          
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
          
          <button 
            v-if="hasActiveFilters"
            @click="clearFilters"
            class="clear-button"
          >
            Clear Filters
          </button>
        </div>
      </div>
      
      <PhotoGallery :photos="filteredPhotos" :loading="loading" @delete-photo="handleDeletePhoto" />
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import PhotoGallery from './components/PhotoGallery.vue'
import { getPhotos, deletePhoto } from './api/photos'

export default {
  name: 'App',
  components: {
    PhotoGallery
  },
  setup() {
    const photos = ref([])
    const loading = ref(false)
    const searchQuery = ref('')
    const selectedAlbum = ref('')
    const startDate = ref('')
    const endDate = ref('')
    const albums = ref([])

    const loadPhotos = async () => {
      loading.value = true
      try {
        photos.value = await getPhotos()
        extractAlbums()
      } catch (error) {
        console.error('Failed to load photos:', error)
        alert('Failed to load photos. Please try again.')
      } finally {
        loading.value = false
      }
    }

    const extractAlbums = () => {
      albums.value = [...new Set(photos.value.flatMap(photo => 
        photo.albums && Array.isArray(photo.albums) ? photo.albums : []
      ))].sort()
    }

    const hasActiveFilters = computed(() => {
      return searchQuery.value || selectedAlbum.value || startDate.value || endDate.value
    })

    const filteredPhotos = computed(() => {
      let result = photos.value

      // Search filter
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(photo => 
          photo.original_filename?.toLowerCase().includes(query) ||
          photo.title?.toLowerCase().includes(query) ||
          photo.description?.toLowerCase().includes(query)
        )
      }

      // Album filter
      if (selectedAlbum.value) {
        result = result.filter(photo => 
          photo.albums && 
          Array.isArray(photo.albums) && 
          photo.albums.includes(selectedAlbum.value)
        )
      }

      // Date range filter
      if (startDate.value) {
        const start = new Date(startDate.value)
        result = result.filter(photo => {
          const photoDate = new Date(photo.date || photo.uploaded_at)
          return photoDate >= start
        })
      }

      if (endDate.value) {
        const end = new Date(endDate.value)
        end.setHours(23, 59, 59, 999) // Include the entire end date
        result = result.filter(photo => {
          const photoDate = new Date(photo.date || photo.uploaded_at)
          return photoDate <= end
        })
      }

      return result
    })

    const clearFilters = () => {
      searchQuery.value = ''
      selectedAlbum.value = ''
      startDate.value = ''
      endDate.value = ''
    }

    const handleDeletePhoto = async (photoId) => {
      if (confirm('Are you sure you want to delete this photo?')) {
        try {
          await deletePhoto(photoId)
          await loadPhotos()
        } catch (error) {
          console.error('Failed to delete photo:', error)
          alert('Failed to delete photo. Please try again.')
        }
      }
    }

    onMounted(() => {
      loadPhotos()
    })

    return {
      photos,
      filteredPhotos,
      loading,
      searchQuery,
      selectedAlbum,
      startDate,
      endDate,
      albums,
      hasActiveFilters,
      loadPhotos,
      clearFilters,
      handleDeletePhoto
    }
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: #121212;
  padding: 2rem;
}

.header {
  text-align: center;
  color: #e0e0e0;
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 3rem;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
}

.header p {
  font-size: 1.2rem;
  opacity: 0.8;
  color: #b0b0b0;
}

.main {
  max-width: 1400px;
  margin: 0 auto;
}

.filters {
  background: #1e1e1e;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.search-container {
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.search-input::placeholder {
  color: #707070;
}

.filter-group {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-select,
.filter-input {
  padding: 0.75rem 1rem;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 0.95rem;
  transition: border-color 0.2s;
  min-width: 150px;
}

.filter-select:focus,
.filter-input:focus {
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

.clear-button {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  transition: background 0.2s;
}

.clear-button:hover {
  background: #5568d3;
}
</style>
