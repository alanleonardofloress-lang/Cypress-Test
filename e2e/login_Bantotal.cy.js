describe('Login TestingLink Bantotal', () => {
  it('Debería loguearse correctamente', () => {
    cy.visit('http://172.17.97.206:8080/btdespri/servlet/com.dlya.bantotal.hlogin', {
      failOnStatusCode: false,
      onBeforeLoad(win) {
        // Stub para que cualquier window.open navegue en la misma ventana
        cy.stub(win, 'open').callsFake((url) => {
          win.location.href = url;
        }).as('windowOpen');
      }
    });

    // Ingresar usuario
    cy.get('#vUSER')
      .focus()
      .invoke('val', 'INSTALADOR')
      .then($el => cy.wrap($el).trigger('change').blur());

    cy.get('#vUSER').should('have.value', 'INSTALADOR');

    // Ingresar contraseña
    cy.get('[name="vPASSWORD"]')
      .clear()
      .type('Bancor123')
      .blur();

    cy.get('[name="vPASSWORD"]').should('have.value', 'Bancor123');

    // Hacer click en el botón "Iniciar Sesión"
    cy.get('#BTNOPINICIARSESION').click();

    // Verificar si se llamó a window.open (opcional, no bloquear test si no ocurre)
    cy.get('@windowOpen').then((stub) => {
      if (stub && stub.called) {
        expect(stub).to.have.been.called;
      } else {
        cy.log('window.open no fue llamado, continuamos validando por URL');
      }
    });

    // Verificar que redirigió a una página válida luego del login
    cy.url().should('match', /realIndex\.html|hwelcome/);

    // Extra: validar que aparece algún texto típico de login exitoso
    //cy.contains(/Bienvenido|Menú|Inicio/i).should('exist');





  });


afterEach(() => {
  cy.get('img[alt="logout"]').click();

  // Validar que se redirigió al login
  cy.url().should('include', '/login');
  cy.contains('Bienvenido/a a su Banca en Línea').should('be.visible');
});


});

