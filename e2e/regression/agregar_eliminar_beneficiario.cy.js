describe('Login BSE - Banco ', () => {
  it('Debe agregar un beneficiario y eliminarlo', () => {

    //  Login 
    cy.loginBSE('silvana25', 'Sil1208')  


    //  esperar a que se vea transferencias
   cy.contains('p', 'Transferencias').click();


  // hacer clic en la opción "Administración"
cy.contains('Administración').click();


//hacer clic en agregar beneficiario
cy.get('.product-actions > .secondary').click();


cy.get('.spinner', { timeout: 50000 }).should('not.exist');


cy.get('.input-cont > .input > .ng-tns-c32-3', { timeout: 50000 })
      .first()
      .should('be.visible')
      .clear()
      .type('dai.cc3')


cy.get('.secondary').click()


cy.get('.additional-item-header').should('exist');


cy.get('.input-cont > .input > .ng-tns-c32-4')
      .first()
      .should('be.visible')
      .clear()
      .type('aflores@accionpoint.com')



cy.get('.input-cont > .input > .ng-tns-c32-5')
      .clear()
      .type('automation')



cy.contains('button', 'Continuar').click();



cy.get(':nth-child(2) > h2').should('be.visible')



cy.get('.margin-top > .secondary').click()



cy.get('.terciary', { timeout: 20000 }).click()


  //  esperar a que se vea transferencias
   cy.contains('p', 'Transferencias').click();


 // hacer clic en la opción "Administración"
cy.contains('Administración').click();


cy.contains('td', 'BLANCO DAIANA')
  .should('be.visible')
  .click();


  // 2. Verificar que el modal se abre con el nombre correcto
cy.get('.data .cut') 
  .should('contain.text', 'BLANCO DAIANA');


  // 3. Cerrar el modal (buscando el botón de cerrar "X")
cy.get('.header cross-svg.pointer')
  .filter(':visible')
  .click({ force: true });


// Buscar la fila que contenga "BLANCO DAIANA"
cy.contains('tr', 'BLANCO DAIANA')
  .should('be.visible') 
  .find('div.table-actions svg')   //div.table-actions svg
  .click({ force: true });


cy.get('button.secondary.flat').first().click({ force: true });


//hace scrool para hacer aparecer nuevamente X
//cy.get('.header.canClose cross-svg.close')
// .scrollIntoView()
// .click({ force: true });


// Buscar la fila que contenga "BLANCO DAIANA"
//cy.contains('tr', 'BLANCO DAIANA')
 // .should('be.visible') 
 // .find('div.table-actions svg')   //div.table-actions svg
 // .click({ force: true });

 // cy.get('button.secondary.flat').first().click({ force: true });

  // 2. Esperar que aparezca el modal/alerta 
cy.get('.alert', { timeout: 10000 })
  .should('be.visible')
 .and('contain.text', 'Listo');




  })



afterEach(() => {
  cy.get('img[alt="logout"]').click();

  // Validar que se redirigió al login
  cy.url().should('include', '/login');
  cy.contains('Bienvenido/a a su Banca en Línea').should('be.visible');
});


})