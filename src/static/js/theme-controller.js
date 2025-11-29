class LayoutCustomizer {
  constructor() {
    this.defaultConfig = {
      theme: "light"
    }

    const configCache = localStorage.getItem("__GRUGSTACK_CONFIG_v0.1__")

    if (configCache) {
      this.config = JSON.parse(configCache)
    } else {
      this.config = { ...this.defaultConfig }
    }
    this.html = document.documentElement
  }

  updateTheme = () => {
    localStorage.setItem("__GRUGSTACK_CONFIG_v0.1__", JSON.stringify(this.config))
    this.html.setAttribute("data-theme", this.config.theme)
  }

  syncCheckboxState = () => {
    const themeControls = document.querySelectorAll("[data-theme-control]")
    themeControls.forEach((control) => {
      if (control.type === "checkbox" && control.getAttribute("data-theme-control") === "toggle") {
        control.checked = this.config.theme === "dark"
      }
    })
  }

  initEventListener = () => {
    const themeControls = document.querySelectorAll("[data-theme-control]")
    themeControls.forEach((control) => {
      const controlValue = control.getAttribute("data-theme-control")

      // Handle checkbox toggles
      if (control.type === "checkbox" && controlValue === "toggle") {
        control.addEventListener("change", () => {
          this.config.theme = control.checked ? "dark" : "light"
          this.updateTheme()
        })
      }
      // Handle button-based toggles (backward compatibility)
      else {
        control.addEventListener("click", () => {
          let theme = controlValue ?? "light"
          if (theme === "toggle") {
            theme = this.config.theme === "light" ? "dark" : "light"
          }
          this.config.theme = theme
          this.updateTheme()
          this.syncCheckboxState()
        })
      }
    })
  }

  afterInit = () => {
    this.syncCheckboxState()
    this.initEventListener()
  }

  init = () => {
    this.updateTheme()
    window.addEventListener("DOMContentLoaded", this.afterInit)
  }
}

new LayoutCustomizer().init()
