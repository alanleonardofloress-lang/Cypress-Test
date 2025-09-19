describe('Trajeta de credito ', () => {
  it('Verificar que exista tarjeta de credito', () => {

    //  Login 
    cy.loginBSE('Prisma1', 'Btest1')  


// selecciona la tarjeta de crédito
cy.get('.title-cont > .name', { timeout: 10000 })
  .should('be.visible')
  .click();

// verificar que existan movimientos
cy.get('.col12.margin-top-small.animate__fadeIn')
  .should('be.visible')
  .and('contain.text', 'Fecha')
  .and('contain.text', 'Monto');

// ingreso a detalle
cy.contains('div.tab', 'Detalle de la tarjeta').click();

// verificar que exista detalle
cy.get('.col12.ng-star-inserted > .row', { timeout: 10000 })
  .should('be.visible');



      });

   afterEach(() => {
  cy.get('img[alt="logout"]').click();

  // Validar que se redirigió al login
  cy.url().should('include', '/login');
  cy.contains('Iniciar sesión').should('be.visible');
});

});


