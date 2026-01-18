import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "home",
    component: () => import("../views/HomePage.vue"),
  },
  {
    path: "/search",
    name: "search",
    component: () => import("../views/SearchPage.vue"),
  },
  {
    path: "/photos/:uuid",
    name: "photo-detail",
    component: () => import("../views/PhotoDetailPage.vue"),
    props: true,
  },
  {
    path: "/map",
    name: "map-view",
    component: () => import("../views/PhotoMapView.vue"),
  },
  {
    path: "/version",
    name: "version",
    component: () => import("../views/VersionPage.vue"),
  },
  {
    path: "/settings/apple",
    name: "apple-settings",
    component: () => import("../views/AppleSettingsPage.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
