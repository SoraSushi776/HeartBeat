import { createApp } from "vue"
import App from "./App.vue"
import { DashboardStore, DashboardKey } from "./stores/dashboard"
import { router } from "./router"
import "./styles/tokens.css"
import "./styles/base.css"

const app = createApp(App)
app.use(router)
app.provide(DashboardKey, new DashboardStore())
app.mount("#app")
