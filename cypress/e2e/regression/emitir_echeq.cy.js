describe('Emitir ECHEQ', () => {

    // logout
     afterEach(() => {
    cy.get('img[alt="logout"]').click();
  });



  it('Emitir un ECHEQ a un tercero', () => {

    //  Login 
    cy.loginBSE('silvana25', 'Sil1208')  


    //  esperar a que se vea Chequeras
   cy.contains('p', 'Chequeras').click();


   // hacer clic en el submenú "Emisión de eCheq"
   cy.get(':nth-child(2) > :nth-child(4) > .not-styled > p', { timeout: 10000 })
   .should('be.visible')
   .click();


  // desplegar el select de cuentas
  cy.get('div.account-select').click({ force: true });


    // esperar a que aparezca la lista
    cy.get(':nth-child(1) > .account',{ timeout: 10000 })
    .should('have.length.greaterThan', 0)  // confirma que hay cuentas
    .first()
    .click();


    // hacer input del cuit del beneficiario
    cy.get('.input-cont > .input > .ng-tns-c32-5')
    .should('be.visible')
    .clear()
    .type('27368914733');


    // hacer clic en "comprobar"
    cy.contains('button', 'Comprobar').click();


    // esperar a que cargue los datos del beneficiario
    cy.get('.additional-item-header', { timeout: 10000 })
    .should('contain.text', 'Datos del beneficiario');


    // ingresar el importe
    cy.get('input[placeholder="0,00"]').type('12500');


    // seleccionar el tipo de cheque
    cy.get(':nth-child(6) > .ng-tns-c151-3 > .wrapper > .combo-cont> .small> svg').click();


    // seleccionar echeq comun
    cy.get(':nth-child(6) > .ng-tns-c151-3 > .wrapper > .options-cont > :nth-child(1)').click();


    // desplegar el concepto
   cy.get(':nth-child(7) > .ng-tns-c151-3 > .wrapper > .combo-cont> .small> svg').click();


    // seleccionar el concepto "NO A LA ORDEN"
    cy.get(':nth-child(7) > .ng-tns-c151-3 > .wrapper > .options-cont > :nth-child(2)').click();


    // ingresar el mail del beneficiario
       cy.get('.input-cont > .input > .ng-tns-c32-7')
      .should('be.visible')
      .clear()
      .type('aflores@accionpoint.com');


    // ingresar una refencia
    cy.get('.input-cont > .input > .ng-tns-c32-8')
    .should('be.visible')
    .clear()
    .type('automation');
    
    
    // hacer clic en continuar
    cy.contains('button', 'Continuar').click();


    // verificar que se esté en la pantalla de confirmación
    cy.get(':nth-child(2) > h2', { timeout: 10000 })
    .should('contain.text', 'Confirmación');


    // hacer clic en confirmar
    cy.get(':nth-child(6) > .secondary').click();


    // verificar la pantalla de emisios de echeq
    cy.get('.operation-type > .gray', { timeout: 10000 })
    .should('contain.text', 'Operación finalizada con éxito');




   });

});