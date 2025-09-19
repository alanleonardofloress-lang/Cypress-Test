const { defineConfig } = require("cypress");
const fs = require("fs");
const sql = require("mssql");

module.exports = defineConfig({
  e2e: {
    specPattern: "e2e/**/*.cy.js",
    supportFile: "support/e2e.js",
    viewportWidth: 1366,
    viewportHeight: 768,

    setupNodeEvents(on, config) {
      console.log("✅ Cypress cargó el setupNodeEvents correctamente");

      // 🔹 Tareas personalizadas
      on("task", {
        // 👉 eliminar archivos
        deleteFile(filePath) {
          if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
            return true;
          }
          return false;
        },

        // 👉 ejecutar queries en SQL Server
       dbQuery: async (query) => {
  try {
    const pool = await sql.connect({
      user: "usrbttestlinkread",
      password: "NfvrfwqP2qAUfMRFF7GG",
      server: "10.250.20.114",
      database: "testinglink",
      options: {
        encrypt: false,
        trustServerCertificate: true
      }
    });

    const result = await pool.request().query(query);
    return result.recordset;
  } catch (err) {
    //  Lanza el error para que Cypress lo marque como fallo
    throw new Error(`Error en la query: ${err.message}`);
  }


        },
      });
    },

    downloadsFolder: "cypress/downloads",
  },
});

