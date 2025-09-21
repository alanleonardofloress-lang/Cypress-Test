describe('Login BSE - Banco Santiago', () => {
  it('Debe loguearse correctamente con usuario válido', () => {
    cy.loginBSE('silvana25', 'Sil1208')  
  })
})

