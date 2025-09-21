describe('Login BSE - Banco Santiago', () => {
  it('Debe loguearse y constituir un Plazo Fijo', () => {
    // se define ruta del archivo esperado
    const downloadsFolder = 'cypress/downloads'
    const fileName = 'Términos y condiciones.pdf'
    const filePath = "cypress/downloads/Términos y condiciones.pdf"

    //  Login 
    cy.loginBSE('silvana25', 'Sil1208')  

    // 1. Espera a que aparezca el botón Constituir
    cy.contains('Constituir', { timeout: 10000 }).should('be.visible')

    // 2. Hacer clic en el botón Constituir
    cy.contains('Constituir').click()

    // 3. Esperar a que aparezca el título
    cy.contains('Seleccione una cuenta origen', { timeout: 30000 }).should('be.visible')

    // 3.1 Esperar a que desaparezca el loader
    cy.get('.loader-container', { timeout: 20000 }).should('not.exist')

    // 4. Hacer clic en el desplegable de cuentas
    cy.get('.account-select', { timeout: 20000 }).click()

    // 5. Seleccionar la primera cuenta desplegada
    cy.get('.account', { timeout: 20000 }).first().click()


   cy.selectFirstOptionFromCombo('[title="Seleccione una opción"]', 'p.remove-margin');


    // 8. Ingresar monto
    cy.get('input[type="text"][format="import"]', { timeout: 20000 })
      .first()
      .should('be.visible')
      .clear()
      .type('15465')

    // 9. Ingresar plazo en días
    cy.get('input[type="text"][maxlength="5"]', { timeout: 20000 })
      .should('be.visible')
      .clear()
      .type('30')

    // 10. Abrir combo "Instrucción al vencimiento"
    cy.contains('p', 'Seleccione una opción', { timeout: 20000 })
      .should('be.visible')
      .click({ force: true })

    // 11. Seleccionar la primera opción
    cy.get(':nth-child(7) > app-combobox > .wrapper > .options-cont > :nth-child(1) > .remove-margin')
      .click({ force: true })

    // 12. Hacer clic en "Simular"
    cy.get('button.secondary', { timeout: 20000 })
      .should('be.visible')
      .and('not.be.disabled')
      .click()

    // Validar que aparece la confirmación
    cy.contains('h2', 'Confirmación').should('be.visible')

    // 13. Click en T&C
    cy.get('.link').should('be.visible').click()

    // 14. Descargar T&C
    cy.get('app-download-button.flat > .download').click()

    // 15. Verificar que el archivo se descargó
    cy.readFile(filePath, { timeout: 15000 }).should("exist")

    // 16. Eliminar el archivo descargado
    cy.task('deleteFile', filePath).then((deleted) => {
    expect(deleted).to.be.true
    })

    // 17. Aceptar T&C
    cy.get('.col12 > .multi-buttons > .secondary').click()





  })


afterEach(() => {
  cy.get('img[alt="logout"]').click();

  // Validar que se redirigió al login
  cy.url().should('include', '/login');
  cy.contains('Bienvenido/a a su Banca en Línea').should('be.visible');
});


})
