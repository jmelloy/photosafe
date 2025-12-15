<template>
  <div class="app">
    <!-- Show version page without authentication if on /version route -->
    <RouterView v-if="isVersionPage" />

    <!-- Show auth screens if not authenticated -->
    <Login
      v-else-if="!isAuthenticatedRef && currentView === 'login'"
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

      <!-- Router view for different pages -->
      <RouterView />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import Login from "./components/Login.vue";
import Register from "./components/Register.vue";
import { isAuthenticated, getCurrentUser, logout } from "./api/auth";
import type { User } from "./types/api";

const currentView = ref<"login" | "register">("login");
const currentUser = ref<User | null>(null);
const isAuthenticatedRef = ref<boolean>(isAuthenticated());
const router = useRouter();
const route = useRoute();

const isVersionPage = computed(() => route.path === '/version');

const loadCurrentUser = async () => {
  try {
    currentUser.value = await getCurrentUser();
  } catch (error) {
    console.error("Failed to load current user:", error);
  }
};

const handleLoginSuccess = async () => {
  isAuthenticatedRef.value = true;
  await loadCurrentUser();
  // Navigate to home after login
  router.push("/");
};

const handleLogout = () => {
  logout();
  currentUser.value = null;
  currentView.value = "login";
  isAuthenticatedRef.value = false;
  // Navigate to home after logout (will show login)
  router.push("/");
};

onMounted(() => {
  if (isAuthenticatedRef.value) {
    loadCurrentUser();
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
</style>
