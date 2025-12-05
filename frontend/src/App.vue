<template>
  <div class="app">
    <header class="header">
      <h1>📷 PhotoSafe Gallery</h1>
      <p>Your personal photo collection</p>
    </header>
    
    <main class="main">
      <PhotoUpload @photo-uploaded="loadPhotos" />
      <PhotoGallery :photos="photos" :loading="loading" @delete-photo="handleDeletePhoto" />
    </main>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import PhotoUpload from './components/PhotoUpload.vue'
import PhotoGallery from './components/PhotoGallery.vue'
import { getPhotos, deletePhoto } from './api/photos'

export default {
  name: 'App',
  components: {
    PhotoUpload,
    PhotoGallery
  },
  setup() {
    const photos = ref([])
    const loading = ref(false)

    const loadPhotos = async () => {
      loading.value = true
      try {
        photos.value = await getPhotos()
      } catch (error) {
        console.error('Failed to load photos:', error)
        alert('Failed to load photos. Please try again.')
      } finally {
        loading.value = false
      }
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
      loading,
      loadPhotos,
      handleDeletePhoto
    }
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.header {
  text-align: center;
  color: white;
  margin-bottom: 3rem;
}

.header h1 {
  font-size: 3rem;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.header p {
  font-size: 1.2rem;
  opacity: 0.9;
}

.main {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
