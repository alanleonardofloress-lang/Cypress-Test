// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

//Login
Cypress.Commands.add('loginBSE', (usuario, password) => {
  cy.visit('http://10.250.20.200:4202/BSE/login')
  cy.get('input[placeholder="Ingrese usuario"]').type(usuario)
  cy.get('input[placeholder="Ingrese contraseña"]').type(password)
  cy.contains('Continuar').click()
  cy.url({ timeout: 10000 }).should('include', '/home')
  cy.contains('Posición Global', { timeout: 10000 }).should('be.visible')
})


//combo selector
Cypress.Commands.add('selectFirstOptionFromCombo', (comboSelector, optionSelector) => {
  cy.get(comboSelector)
    .click({ force: true });

  cy.get(optionSelector, { timeout: 10000 })
    .should('have.length.at.least', 1)
    .first()
    .scrollIntoView()
    .should('be.visible')
    .click({ force: true });
});

