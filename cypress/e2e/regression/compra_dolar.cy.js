describe('Compra de moneda extranjera', () => {

    // logout
    // afterEach(() => {
  //  cy.get('img[alt="logout"]').click();
 // });


  it('Compra de moneda extranjera', () => {

    //  Login 
    cy.loginBSE('silvana25', 'Sil1208')  


    //  esperar a que se vea "inversiones"
    cy.get(':nth-child(7) > .not-styled > p').click();


    // hacer clic en el submenú "Compra / Venta de moneda extranjera"
     cy.contains('p', 'Compra Venta de Moneda Extranjera').click();



   // verificar que se carga compra/ venta de moneda extranjera
   cy.get('.col12 > .title', { timeout: 10000 })
   .should('be.visible')


   // hacer clic en checkbox de "Compra"
   cy.get('.options-cont > :nth-child(1)', { timeout: 10000 }).click();


   // desplegar el select de cuentas de origen
   cy.get('div.account-select').click({ force: true });


    // esperar a que aparezca la lista
    cy.get(':nth-child(1) > .account',{ timeout: 10000 })
    .should('have.length.greaterThan', 0)  // confirma que hay cuentas
    .first()
    .click();


    // desplegar el selector de cuenta de destino
     cy.get(':nth-child(3) > app-account-selector > .row > :nth-child(2) > .account-select').click({ force: true });


    // esperar a que aparezca la lista
    cy.get(':nth-child(1) > .account',{ timeout: 10000 })
    .should('have.length.greaterThan', 0)  // confirma que hay cuentas
    .last()
    .click();


    // ingresar el importe a comprar
    cy.get('input[placeholder="0,00"]').type('3');


    // hacer clic en la declaración jurada
    cy.contains('label.wrapper.checkbox', 'declaración jurada de compra venta de Moneda Extranjera').click();

    });


    });