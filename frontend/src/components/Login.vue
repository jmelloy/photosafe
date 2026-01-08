<template>
  <div class="login-container">
    <div class="login-card">
      <h2>📷 PhotoSafe Login</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Username</label>
          <input id="username" v-model="username" type="text" required autocomplete="username"
            placeholder="Enter your username" />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input id="password" v-model="password" type="password" required autocomplete="current-password"
            placeholder="Enter your password" />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button type="submit" :disabled="loading" class="login-button">
          {{ loading ? "Logging in..." : "Login" }}
        </button>
      </form>

      <div class="register-link">
        <p>
          Don't have an account?
          <a href="#" @click.prevent="$emit('switch-to-register')">Register</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { login } from "../api/auth";

interface LoginEmits {
  (e: "login-success"): void;
  (e: "switch-to-register"): void;
}

const emit = defineEmits<LoginEmits>();

const username = ref<string>("");
const password = ref<string>("");
const error = ref<string>("");
const loading = ref<boolean>(false);

const handleLogin = async () => {
  error.value = "";
  loading.value = true;

  try {
    console.log("[Login] Attempting login for user:", username.value);
    await login(username.value, password.value);
    console.log("[Login] Login successful");
    emit("login-success");
  } catch (err: any) {
    console.error("Login error:", err);
    console.error("Login error details:", {
      message: err.message,
      response: err.response,
      status: err.response?.status,
      data: err.response?.data,
    });
    if (err.response?.status === 401) {
      error.value = "Invalid username or password";
    } else if (
      err.code === "ECONNREFUSED" ||
      err.message?.includes("Network Error")
    ) {
      error.value = "Cannot connect to server. Is the backend running?";
    } else {
      error.value = `An error occurred: ${err.message || "Please try again."}`;
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #121212;
  padding: 1rem;
}

.login-card {
  background: #1e1e1e;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 400px;
}

.login-card h2 {
  color: #e0e0e0;
  text-align: center;
  margin-bottom: 2rem;
  font-size: 1.8rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  color: #b0b0b0;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.error-message {
  background: #ff4444;
  color: white;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.login-button {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.2s;
}

.login-button:hover:not(:disabled) {
  background: #5568d3;
}

.login-button:disabled {
  background: #4a4a4a;
  cursor: not-allowed;
}

.register-link {
  margin-top: 1.5rem;
  text-align: center;
}

.register-link p {
  color: #b0b0b0;
  font-size: 0.9rem;
}

.register-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>
