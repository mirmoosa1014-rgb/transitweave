const { defineConfig } = require("@playwright/test");
module.exports = defineConfig({
  testDir: "./tests/browser",
  timeout: 30000,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:18766",
    viewport: { width: 1440, height: 1100 },
    launchOptions: { args: ["--no-sandbox"] },
  },
  webServer: {
    command: `${process.env.TRANSITWEAVE_PYTHON || ".venv/bin/python"} -m transitweave.server --port 18766`,
    url: "http://127.0.0.1:18766/api/meta",
    reuseExistingServer: false,
    timeout: 30000,
  },
});
