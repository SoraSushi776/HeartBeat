import { createApp } from "vue"
import App from "./App.vue"
import { DashboardStore, DashboardKey } from "./stores/dashboard"
import "./styles/tokens.css"
import "./styles/base.css"

const app = createApp(App)
app.provide(DashboardKey, new DashboardStore())
app.mount("#app")
