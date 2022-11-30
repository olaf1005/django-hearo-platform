describe('Test registration', function () {
    const testUserName = "Test";
    const testUserCity = "Nairobi, Kenya";
    const testUserEmail = "daniel@cache.sh";
    const testUserPassword = "password";
    const testEnv = "DJANGO_SETTINGS_MODULE=settings.test PG_USER=hearo_production PG_HOST=localhost"
    before(() => {
        const setup = "source scripts/init.sh && cd django_app && DJANGO_SETTINGS_MODULE=settings.test PG_USER=hearo_production PG_HOST=localhost";
        // reset and seed the database prior to every test
        // test with test seed
        cy.exec(`${setup} pg_kill_connections hearo_test`);
        cy.exec(`${setup} ./manage.py reset_db --noinput`);
        cy.exec(`${setup} ./manage.py migrate --noinput`);
        cy.exec(`${setup} ./manage.py loaddata tests/fixtures/sites.json`);
    });
    it('successfully loads', function () {
        cy.visit('/');
    });
    it('goes to registration page', function(){
        cy.visit('/');
        cy.get('a[class="button primary large"]:first').click();
        cy.location('pathname').should('eq', '/join/');
    });
    it.only('register as fan', function(){
        cy.visit('/join/');
        cy.get('#fan').click();
        cy.get('input[name=name]').type(testUserName);
        cy.get('input[name=city]').type(testUserCity);
        cy.get('#email').type(testUserEmail);
        cy.get('#password').type(testUserPassword);
        cy.get('#accept').click({force: true});
        cy.get('#initial-signup').click();
        cy.get('a.next-btn').click();
        cy.contains('Finish').click()
        cy.location('pathname').should('eq', '/');
    });
});
