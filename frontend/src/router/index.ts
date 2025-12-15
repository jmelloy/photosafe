import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "home",
    component: () => import("../views/HomePage.vue"),
  },
  {
    path: "/photos/:uuid",
    name: "photo-detail",
    component: () => import("../views/PhotoDetailPage.vue"),
    props: true,
  },
  {
    path: "/version",
    name: "version",
    component: () => import("../views/VersionPage.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
