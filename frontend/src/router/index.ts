import { createRouter, createWebHashHistory, type RouteRecordRaw } from "vue-router"
import HomeView from "../pages/HomeView.vue"
import ProfileView from "../pages/ProfileView.vue"
import DiaryView from "../pages/DiaryView.vue"
import MessagesView from "../pages/MessagesView.vue"

const routes: RouteRecordRaw[] = [
  { path: "/", name: "home", component: HomeView, meta: { title: "实时" } },
  { path: "/profile", name: "profile", component: ProfileView, meta: { title: "主页" } },
  { path: "/diary", name: "diary", component: DiaryView, meta: { title: "日记" } },
  { path: "/diary/:id", name: "diary-entry", component: DiaryView, meta: { title: "日记", nav: false } },
  { path: "/messages", name: "messages", component: MessagesView, meta: { title: "留言" } },
  { path: "/:pathMatch(.*)*", redirect: "/" },
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export const NAV_ITEMS = routes
  .filter((route) => route.name && route.meta?.nav !== false)
  .map((route) => ({
    name: String(route.name),
    path: route.path,
    title: String(route.meta?.title ?? route.name),
  }))
