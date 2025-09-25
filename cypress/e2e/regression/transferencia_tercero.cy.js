describe('Transferencia a tercero', () => {
  it('Realizar una transferencia a tercero', () => {

    //  Login 
    cy.loginBSE('silvana25', 'Sil1208')  


    //  esperar a que se vea transferencias
   cy.contains('p', 'Transferencias').click();


   
   // hacer clic en la opción "transferencias a terceros"
   cy.get(':nth-child(3) > .not-styled > p').click();

   //despliega el menú de cuentas
   cy.get('div.account-select').click({ force: true });


   // esperar a que aparezca la lista
   cy.get(':nth-child(1) > .account',{ timeout: 10000 })
   .should('have.length.greaterThan', 0)  // confirma que hay cuentas
   .first()
   .click();


   cy.get('.beneficiary-select').click({ force: true });


   cy.get(':nth-child(1) > app-beneficiary-others > .beneficiary').click();


   cy.get('.additional-item-header', { timeout: 10000 })
   .should('contain.text', 'Datos del beneficiario');



   cy.get('input[placeholder="0,00"]').type('12125');


   cy.get('.combo-cont').click();


   cy.get('.options-cont > :nth-child(1)').click();


   cy.get('input[type="text"][maxlength="100"]').type('automation');


   cy.get('.secondary').click();


   cy.get(':nth-child(2) > h2', { timeout: 10000 })
   .should('contain.text', 'Confirmación');


   cy.get(':nth-child(6) > .secondary').click();



   cy.get('app-ticket-header > .row', { timeout: 10000 })
   .should('contain.text', 'Transferencia a terceros');



});

});